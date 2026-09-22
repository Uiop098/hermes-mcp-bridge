# Hermes MCP Bridge

Connect and control a remote Hermes agent (on GitHub Codespace) from your local Hermes (on Termux/anywhere).

## Quick Start (On Codespace)

```bash
# Clone the repo
git clone https://github.com/Uiop098/hermes-mcp-bridge.git
cd hermes-mcp-bridge

# Run automated setup
chmod +x setup.sh
./setup.sh
```

The setup script will:
1. Check/install Python and Hermes
2. Install Python dependencies
3. Install and start cloudflared tunnel
4. Start the MCP server
5. Display the connection URL

**Copy the URL** and add it to your **local Hermes config** (`~/.hermes/config.yaml`):

```yaml
mcp:
  servers:
    codespace-hermes:
      transport: sse
      url: "https://xxx.trycloudflare.com/sse"
      timeout: 300
```

Then reload: `hermes config reload`

## Usage (From Local Hermes)

Once connected, you can control the Codespace Hermes:

### Execute Terminal Commands
```
Run "git status" on Codespace
```

### Send Hermes Prompts
```
Tell Codespace Hermes to create a Python Flask app
```

### File Operations
```
Read /workspaces/project/README.md from Codespace
Write a new file on Codespace at ~/test.py with: print("hello")
```

### Get Environment Info
```
Get Codespace environment information
```

## Management Scripts

```bash
# Check status
./status.sh

# View logs
tail -f mcp-server.log
tail -f tunnel.log

# Stop services
./stop.sh

# Restart
./stop.sh && ./setup.sh
```

## Available MCP Tools

1. **execute_hermes_command** - Send prompts to remote Hermes
2. **execute_terminal_command** - Run shell commands on Codespace
3. **read_file** - Read files from Codespace
4. **write_file** - Write files to Codespace
5. **get_codespace_info** - Get environment details

## Architecture

```
[Local Hermes (Termux)]
        ↓ MCP/SSE
[Cloudflare Tunnel]
        ↓ HTTPS
[MCP Server (Codespace)]
        ↓
[Remote Hermes + Terminal]
```

## Files

- `server.py` - MCP server implementation
- `requirements.txt` - Python dependencies
- `setup.sh` - Automated setup script
- `stop.sh` - Stop all services
- `status.sh` - Check service status

## Troubleshooting

### Connection Failed
- Check services: `./status.sh`
- Check logs: `tail -f mcp-server.log tunnel.log`
- Restart: `./stop.sh && ./setup.sh`

### Tunnel URL Changed
- Get new URL: `grep https tunnel.log`
- Update local config: `~/.hermes/config.yaml`
- Reload: `hermes config reload`

### Hermes Not Found
- Install: `curl -fsSL https://install.hermes.nousresearch.com | bash`
- Or: `pip3 install hermes-agent`

## Security Notes

⚠️ This server has full access to your Codespace environment. Only use:
- In temporary/test Codespaces
- With trusted clients
- Behind Cloudflare tunnel (not exposed directly)

For production use, add authentication and access controls.

## License

MIT
