#!/bin/bash

# Cloudflare Tunnel CLI Setup Script
# Automated setup for Ollama API Gateway
# Based on manual CLI setup process

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TUNNEL_NAME="ollama-gateway"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="$SCRIPT_DIR"
CONFIG_FILE="$CONFIG_DIR/config.yml"
CREDENTIALS_DEST="$CONFIG_DIR/credentials.json"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Cloudflare Tunnel CLI Setup${NC}"
echo -e "${BLUE}Automated Setup for Ollama API Gateway${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Check if cloudflared is installed
echo -e "${YELLOW}Step 1: Checking cloudflared installation...${NC}"
if ! command -v cloudflared &> /dev/null; then
    echo -e "${RED}cloudflared is not installed${NC}"
    echo "Installing cloudflared..."
    
    if command -v snap &> /dev/null; then
        echo "Installing via snap..."
        sudo snap install cloudflared
    elif command -v apt-get &> /dev/null; then
        echo "Installing via binary download..."
        BINARY_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        sudo wget -O /usr/local/bin/cloudflared "${BINARY_URL}"
        sudo chmod +x /usr/local/bin/cloudflared
    else
        echo -e "${RED}Please install cloudflared manually:${NC}"
        echo "  https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
        exit 1
    fi
    
    if command -v cloudflared &> /dev/null; then
        echo -e "${GREEN}✓ cloudflared installed successfully${NC}"
        cloudflared --version
    else
        echo -e "${RED}✗ Installation failed${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ cloudflared is installed${NC}"
    cloudflared --version
fi
echo ""

# Step 2: Check authentication
echo -e "${YELLOW}Step 2: Checking Cloudflare authentication...${NC}"
if ! cloudflared tunnel list &> /dev/null; then
    echo -e "${YELLOW}Not authenticated. Opening browser for login...${NC}"
    cloudflared tunnel login
else
    echo -e "${GREEN}✓ Already authenticated${NC}"
fi
echo ""

# Step 3: Create or use existing tunnel
echo -e "${YELLOW}Step 3: Setting up tunnel...${NC}"
if cloudflared tunnel list | grep -q "$TUNNEL_NAME"; then
    echo -e "${YELLOW}Tunnel '$TUNNEL_NAME' already exists${NC}"
    TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
    echo -e "${GREEN}✓ Using existing tunnel: $TUNNEL_ID${NC}"
else
    echo "Creating tunnel: $TUNNEL_NAME"
    TUNNEL_OUTPUT=$(cloudflared tunnel create "$TUNNEL_NAME" 2>&1)
    TUNNEL_ID=$(echo "$TUNNEL_OUTPUT" | grep -oP 'Created tunnel \K[^\s]+' || \
                cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
    
    if [ -z "$TUNNEL_ID" ]; then
        echo -e "${RED}✗ Failed to create tunnel${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Created tunnel: $TUNNEL_ID${NC}"
fi
echo ""

# Step 4: Get domain from user
echo -e "${YELLOW}Step 4: Domain configuration${NC}"
read -p "Enter your domain name (e.g., api.laserpointlabs.com): " DOMAIN_NAME

if [ -z "$DOMAIN_NAME" ]; then
    echo -e "${RED}Error: Domain name is required${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Domain: $DOMAIN_NAME${NC}"
echo ""

# Step 5: Create DNS route
echo -e "${YELLOW}Step 5: Creating DNS route...${NC}"
if cloudflared tunnel route dns "$TUNNEL_NAME" "$DOMAIN_NAME" 2>&1; then
    echo -e "${GREEN}✓ DNS route created${NC}"
else
    echo -e "${YELLOW}⚠ DNS route may already exist or failed to create${NC}"
    echo "  You may need to create it manually in Cloudflare dashboard"
fi
echo ""

# Step 6: Copy credentials file
echo -e "${YELLOW}Step 6: Copying credentials...${NC}"
CREDENTIALS_SOURCE="$HOME/.cloudflared/${TUNNEL_ID}.json"

if [ -f "$CREDENTIALS_SOURCE" ]; then
    cp "$CREDENTIALS_SOURCE" "$CREDENTIALS_DEST"
    # Set permissions so Docker container can read it
    chmod 644 "$CREDENTIALS_DEST"
    echo -e "${GREEN}✓ Credentials copied to $CREDENTIALS_DEST${NC}"
    echo "  File permissions set to 644 (readable by Docker container)"
else
    echo -e "${RED}✗ Credentials file not found at $CREDENTIALS_SOURCE${NC}"
    echo "  Please ensure the tunnel was created successfully"
    exit 1
fi
echo ""

# Step 7: Create config file
echo -e "${YELLOW}Step 7: Creating configuration file...${NC}"
cat > "$CONFIG_FILE" <<EOF
tunnel: $TUNNEL_ID
credentials-file: /etc/cloudflared/credentials.json

ingress:
  - hostname: $DOMAIN_NAME
    service: http://api_gateway:8000
  - service: http_status:404
EOF

echo -e "${GREEN}✓ Configuration file created: $CONFIG_FILE${NC}"
echo ""

# Step 8: Validate configuration
echo -e "${YELLOW}Step 8: Validating configuration...${NC}"
if cloudflared tunnel --config "$CONFIG_FILE" ingress validate 2>&1; then
    echo -e "${GREEN}✓ Configuration is valid${NC}"
else
    echo -e "${YELLOW}⚠ Configuration validation had warnings (may be normal)${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Configuration:"
echo "  Tunnel Name: $TUNNEL_NAME"
echo "  Tunnel ID: $TUNNEL_ID"
echo "  Domain: $DOMAIN_NAME"
echo "  Config File: $CONFIG_FILE"
echo "  Credentials: $CREDENTIALS_DEST"
echo ""
echo "Next steps:"
echo "1. Start Docker containers:"
echo "   cd $PROJECT_ROOT"
echo "   docker compose up -d"
echo ""
echo "2. Check tunnel status:"
echo "   docker compose ps cloudflared"
echo "   docker compose logs cloudflared"
echo ""
echo "3. Test the endpoint (wait a few minutes for DNS propagation):"
echo "   curl https://$DOMAIN_NAME/health"
echo ""
echo "4. Verify tunnel info:"
echo "   cloudflared tunnel info $TUNNEL_NAME"
echo ""

