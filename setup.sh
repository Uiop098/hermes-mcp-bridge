#!/bin/bash
set -e

echo "================================================"
echo "Hermes MCP Bridge - Automated Setup"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python
echo -e "${YELLOW}[1/6] Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 not found. Installing...${NC}"
    sudo apt-get update && sudo apt-get install -y python3 python3-pip
else
    echo -e "${GREEN}✓ Python3 found: $(python3 --version)${NC}"
fi

# Check Hermes
echo ""
echo -e "${YELLOW}[2/6] Checking Hermes...${NC}"
if ! command -v hermes &> /dev/null; then
    echo -e "${RED}Hermes not found. Installing...${NC}"
    curl -fsSL https://install.hermes.nousresearch.com | bash
    export PATH="$HOME/.hermes/bin:$PATH"
    echo -e "${GREEN}✓ Hermes installed${NC}"
else
    echo -e "${GREEN}✓ Hermes found: $(hermes --version 2>&1 | head -1)${NC}"
fi

# Install Python dependencies
echo ""
echo -e "${YELLOW}[3/6] Installing Python dependencies...${NC}"
pip3 install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Check for cloudflared
echo ""
echo -e "${YELLOW}[4/6] Checking for cloudflared tunnel...${NC}"
if ! command -v cloudflared &> /dev/null; then
    echo -e "${YELLOW}Installing cloudflared...${NC}"
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared
    chmod +x cloudflared
    sudo mv cloudflared /usr/local/bin/
    echo -e "${GREEN}✓ cloudflared installed${NC}"
else
    echo -e "${GREEN}✓ cloudflared found${NC}"
fi

# Start MCP server in background
echo ""
echo -e "${YELLOW}[5/6] Starting MCP server...${NC}"
nohup python3 server.py > mcp-server.log 2>&1 &
MCP_PID=$!
echo $MCP_PID > mcp-server.pid
sleep 3

if ps -p $MCP_PID > /dev/null; then
    echo -e "${GREEN}✓ MCP Server started (PID: $MCP_PID)${NC}"
else
    echo -e "${RED}✗ MCP Server failed to start. Check mcp-server.log${NC}"
    exit 1
fi

# Start cloudflare tunnel
echo ""
echo -e "${YELLOW}[6/6] Starting Cloudflare tunnel...${NC}"
nohup cloudflared tunnel --url http://localhost:8000 > tunnel.log 2>&1 &
TUNNEL_PID=$!
echo $TUNNEL_PID > tunnel.pid
sleep 5

# Extract tunnel URL
TUNNEL_URL=$(grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' tunnel.log | head -1)

if [ -z "$TUNNEL_URL" ]; then
    echo -e "${RED}✗ Failed to get tunnel URL. Check tunnel.log${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Tunnel started (PID: $TUNNEL_PID)${NC}"
echo ""
echo "================================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "================================================"
echo ""
echo -e "${GREEN}MCP Server URL:${NC} ${TUNNEL_URL}/sse"
echo ""
echo -e "${YELLOW}Add this to your LOCAL Hermes config (~/.hermes/config.yaml):${NC}"
echo ""
echo "mcp:"
echo "  servers:"
echo "    codespace-hermes:"
echo "      transport: sse"
echo "      url: \"${TUNNEL_URL}/sse\""
echo "      timeout: 300"
echo ""
echo -e "${YELLOW}Then run:${NC} hermes config reload"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo "  MCP Server: tail -f mcp-server.log"
echo "  Tunnel:     tail -f tunnel.log"
echo ""
echo -e "${YELLOW}Stop services:${NC} ./stop.sh"
echo ""
