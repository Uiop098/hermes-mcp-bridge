#!/bin/bash

echo "Stopping Hermes MCP Bridge services..."

# Stop MCP server
if [ -f mcp-server.pid ]; then
    MCP_PID=$(cat mcp-server.pid)
    if ps -p $MCP_PID > /dev/null; then
        kill $MCP_PID
        echo "✓ MCP Server stopped (PID: $MCP_PID)"
    else
        echo "✗ MCP Server not running"
    fi
    rm mcp-server.pid
fi

# Stop tunnel
if [ -f tunnel.pid ]; then
    TUNNEL_PID=$(cat tunnel.pid)
    if ps -p $TUNNEL_PID > /dev/null; then
        kill $TUNNEL_PID
        echo "✓ Tunnel stopped (PID: $TUNNEL_PID)"
    else
        echo "✗ Tunnel not running"
    fi
    rm tunnel.pid
fi

echo "All services stopped."
