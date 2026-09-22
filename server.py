#!/usr/bin/env python3
"""
MCP Server for Remote Hermes Control
Exposes Hermes agent and terminal on GitHub Codespace to remote MCP clients.
"""
import asyncio
import subprocess
import json
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import Response
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("codespace-hermes-control")

@server.list_tools()
async def list_tools():
    """List available tools for controlling the remote Hermes."""
    return [
        Tool(
            name="execute_hermes_command",
            description="Execute a command or prompt on the remote Hermes agent in the Codespace. Returns Hermes output.",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The instruction/prompt to send to the remote Hermes agent"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default 300)",
                        "default": 300
                    }
                },
                "required": ["prompt"]
            }
        ),
        Tool(
            name="execute_terminal_command",
            description="Execute a shell command on the Codespace terminal. Returns stdout/stderr.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute"
                    },
                    "workdir": {
                        "type": "string",
                        "description": "Working directory (optional, defaults to ~)"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default 180)",
                        "default": 180
                    }
                },
                "required": ["command"]
            }
        ),
        Tool(
            name="read_file",
            description="Read a file from the Codespace filesystem",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute or relative path to the file"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="write_file",
            description="Write content to a file on the Codespace filesystem",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute or relative path to the file"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    }
                },
                "required": ["path", "content"]
            }
        ),
        Tool(
            name="get_codespace_info",
            description="Get information about the Codespace environment (pwd, env vars, running processes)",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool invocations."""
    logger.info(f"Tool called: {name} with args: {arguments}")
    
    try:
        if name == "execute_hermes_command":
            prompt = arguments["prompt"]
            timeout = arguments.get("timeout", 300)
            
            # Execute Hermes with the prompt
            proc = await asyncio.create_subprocess_exec(
                "hermes", prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                result = {
                    "stdout": stdout.decode('utf-8', errors='replace'),
                    "stderr": stderr.decode('utf-8', errors='replace'),
                    "exit_code": proc.returncode
                }
                return [TextContent(
                    type="text",
                    text=f"Hermes output:\n{result['stdout']}\n\nErrors (if any):\n{result['stderr']}\n\nExit code: {result['exit_code']}"
                )]
            except asyncio.TimeoutError:
                proc.kill()
                return [TextContent(type="text", text=f"Command timed out after {timeout} seconds")]
        
        elif name == "execute_terminal_command":
            command = arguments["command"]
            workdir = arguments.get("workdir", "~")
            timeout = arguments.get("timeout", 180)
            
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workdir if workdir != "~" else None
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                result = {
                    "stdout": stdout.decode('utf-8', errors='replace'),
                    "stderr": stderr.decode('utf-8', errors='replace'),
                    "exit_code": proc.returncode
                }
                return [TextContent(
                    type="text",
                    text=f"Command: {command}\n\nOutput:\n{result['stdout']}\n\nErrors:\n{result['stderr']}\n\nExit code: {result['exit_code']}"
                )]
            except asyncio.TimeoutError:
                proc.kill()
                return [TextContent(type="text", text=f"Command timed out after {timeout} seconds")]
        
        elif name == "read_file":
            path = arguments["path"]
            try:
                with open(path, 'r') as f:
                    content = f.read()
                return [TextContent(type="text", text=f"File: {path}\n\n{content}")]
            except Exception as e:
                return [TextContent(type="text", text=f"Error reading file: {str(e)}")]
        
        elif name == "write_file":
            path = arguments["path"]
            content = arguments["content"]
            try:
                with open(path, 'w') as f:
                    f.write(content)
                return [TextContent(type="text", text=f"Successfully wrote {len(content)} bytes to {path}")]
            except Exception as e:
                return [TextContent(type="text", text=f"Error writing file: {str(e)}")]
        
        elif name == "get_codespace_info":
            proc = await asyncio.create_subprocess_shell(
                "echo 'PWD:' && pwd && echo '\nENV:' && env | head -20 && echo '\nPROCESSES:' && ps aux | head -10",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            info = stdout.decode('utf-8', errors='replace')
            return [TextContent(type="text", text=f"Codespace Info:\n{info}")]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Error executing tool {name}: {str(e)}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]

# Setup SSE transport
sse = SseServerTransport("/messages")

async def handle_sse(request):
    """Handle SSE connection requests."""
    logger.info("New SSE connection established")
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())
    return Response()

# Create Starlette app
app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages", app=sse.handle_post_message)
    ]
)

if __name__ == "__main__":
    logger.info("Starting Codespace Hermes MCP Server on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
