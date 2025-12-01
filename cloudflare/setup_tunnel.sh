#!/bin/bash

# Cloudflare Tunnel Setup Script
# This script automates the setup of Cloudflare Tunnel for the Ollama API Gateway

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
TUNNEL_NAME="ollama-gateway"
CONFIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$CONFIG_DIR/.." && pwd)"
CONFIG_FILE="$CONFIG_DIR/config.yml"
CREDENTIALS_DIR="$HOME/.cloudflared"

echo -e "${GREEN}Cloudflare Tunnel Setup for Ollama API Gateway${NC}"
echo "=================================================="
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo -e "${RED}Error: cloudflared is not installed${NC}"
    echo "Please install cloudflared first:"
    echo "  macOS: brew install cloudflared"
    echo "  Linux: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
    exit 1
fi

echo -e "${GREEN}✓ cloudflared is installed${NC}"
echo ""

# Step 1: Authenticate
echo -e "${YELLOW}Step 1: Authenticating with Cloudflare...${NC}"
if [ ! -f "$CREDENTIALS_DIR/cert.pem" ]; then
    echo "Opening browser for authentication..."
    cloudflared tunnel login
else
    echo -e "${GREEN}✓ Already authenticated${NC}"
fi
echo ""

# Step 2: Get domain name
echo -e "${YELLOW}Step 2: Domain Configuration${NC}"
read -p "Enter your domain name (e.g., api.yourdomain.com): " DOMAIN_NAME

if [ -z "$DOMAIN_NAME" ]; then
    echo -e "${RED}Error: Domain name is required${NC}"
    exit 1
fi

echo ""

# Step 3: Create tunnel
echo -e "${YELLOW}Step 3: Creating tunnel...${NC}"
TUNNEL_OUTPUT=$(cloudflared tunnel create "$TUNNEL_NAME" 2>&1)
TUNNEL_ID=$(echo "$TUNNEL_OUTPUT" | grep -oP '(?<=Created tunnel )[a-f0-9-]+' || echo "")

if [ -z "$TUNNEL_ID" ]; then
    # Try to get existing tunnel ID
    TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}' || echo "")
    
    if [ -z "$TUNNEL_ID" ]; then
        echo -e "${RED}Error: Could not create or find tunnel${NC}"
        echo "Output: $TUNNEL_OUTPUT"
        exit 1
    else
        echo -e "${GREEN}✓ Using existing tunnel: $TUNNEL_ID${NC}"
    fi
else
    echo -e "${GREEN}✓ Created tunnel: $TUNNEL_ID${NC}"
fi
echo ""

# Step 4: Create DNS route
echo -e "${YELLOW}Step 4: Creating DNS route...${NC}"
cloudflared tunnel route dns "$TUNNEL_NAME" "$DOMAIN_NAME" || {
    echo -e "${YELLOW}Warning: Could not create DNS route automatically${NC}"
    echo "You may need to create a CNAME record manually:"
    echo "  Name: $DOMAIN_NAME"
    echo "  Value: $TUNNEL_ID.cfargotunnel.com"
    echo ""
    echo "Or run: cloudflared tunnel route dns $TUNNEL_NAME $DOMAIN_NAME"
}
echo ""

# Step 5: Create config file
echo -e "${YELLOW}Step 5: Creating configuration file...${NC}"

# Find credentials file
CREDENTIALS_FILE=$(find "$CREDENTIALS_DIR" -name "${TUNNEL_ID}.json" 2>/dev/null | head -n 1)

if [ -z "$CREDENTIALS_FILE" ]; then
    # Try alternative location
    CREDENTIALS_FILE="$CREDENTIALS_DIR/${TUNNEL_ID}.json"
    if [ ! -f "$CREDENTIALS_FILE" ]; then
        echo -e "${YELLOW}Warning: Credentials file not found at expected location${NC}"
        echo "Please provide the path to the credentials file:"
        read -p "Credentials file path: " CREDENTIALS_FILE
    fi
fi

# Create config.yml
cat > "$CONFIG_FILE" << EOF
tunnel: $TUNNEL_ID
credentials-file: $CREDENTIALS_FILE

ingress:
  - hostname: $DOMAIN_NAME
    service: http://localhost:8000
  - service: http_status:404
EOF

echo -e "${GREEN}✓ Configuration file created: $CONFIG_FILE${NC}"
echo ""

# Step 6: Test configuration
echo -e "${YELLOW}Step 6: Testing configuration...${NC}"
if cloudflared tunnel --config "$CONFIG_FILE" ingress validate; then
    echo -e "${GREEN}✓ Configuration is valid${NC}"
else
    echo -e "${RED}Warning: Configuration validation failed${NC}"
fi
echo ""

# Step 7: Create systemd service (optional)
echo -e "${YELLOW}Step 7: Systemd Service Setup (Optional)${NC}"
read -p "Create systemd service to run tunnel automatically? (y/n): " CREATE_SERVICE

if [[ "$CREATE_SERVICE" =~ ^[Yy]$ ]]; then
    SERVICE_FILE="/etc/systemd/system/cloudflared-tunnel.service"
    
    sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Cloudflare Tunnel for Ollama API Gateway
After=network.target

[Service]
Type=simple
User=$USER
ExecStart=$(which cloudflared) tunnel --config $CONFIG_FILE run
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

    echo -e "${GREEN}✓ Systemd service file created${NC}"
    echo ""
    echo "To enable and start the service:"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable cloudflared-tunnel"
    echo "  sudo systemctl start cloudflared-tunnel"
    echo ""
fi

# Summary
echo ""
echo -e "${GREEN}=================================================="
echo "Setup Complete!"
echo "==================================================${NC}"
echo ""
echo "Tunnel ID: $TUNNEL_ID"
echo "Domain: $DOMAIN_NAME"
echo "Config File: $CONFIG_FILE"
echo ""
echo "To run the tunnel manually:"
echo "  cloudflared tunnel --config $CONFIG_FILE run"
echo ""
echo "Or use the systemd service (if created):"
echo "  sudo systemctl start cloudflared-tunnel"
echo ""
echo -e "${YELLOW}Important:${NC}"
echo "1. Make sure the API Gateway is running on localhost:8000"
echo "2. Ensure DNS propagation is complete (may take a few minutes)"
echo "3. Test the connection: curl https://$DOMAIN_NAME/health"
echo ""

