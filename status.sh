#!/bin/bash

echo "================================================"
echo "Hermes MCP Bridge - Status"
echo "================================================"
echo ""

# Check MCP server
if [ -f mcp-server.pid ]; then
    MCP_PID=$(cat mcp-server.pid)
    if ps -p $MCP_PID > /dev/null; then
        echo "✓ MCP Server: Running (PID: $MCP_PID)"
    else
        echo "✗ MCP Server: Not running (stale PID file)"
    fi
else
    echo "✗ MCP Server: Not running"
fi

# Check tunnel
if [ -f tunnel.pid ]; then
    TUNNEL_PID=$(cat tunnel.pid)
    if ps -p $TUNNEL_PID > /dev/null; then
        echo "✓ Tunnel: Running (PID: $TUNNEL_PID)"
        TUNNEL_URL=$(grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' tunnel.log | head -1)
        if [ ! -z "$TUNNEL_URL" ]; then
            echo "  URL: ${TUNNEL_URL}/sse"
        fi
    else
        echo "✗ Tunnel: Not running (stale PID file)"
    fi
else
    echo "✗ Tunnel: Not running"
fi

echo ""
echo "Recent MCP Server Logs:"
echo "------------------------"
tail -5 mcp-server.log 2>/dev/null || echo "No logs available"

echo ""
echo "Recent Tunnel Logs:"
echo "-------------------"
tail -5 tunnel.log 2>/dev/null || echo "No logs available"
