#!/bin/bash

# Update Cloudflare config.yml from .env file
# This script reads CLOUDFLARE_TUNNEL_URL from .env and updates config.yml

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/cloudflare/config.yml"
ENV_FILE="$PROJECT_ROOT/.env"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Updating Cloudflare config from .env file...${NC}"

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}✗ .env file not found at $ENV_FILE${NC}"
    exit 1
fi

# Get domain from .env
TUNNEL_URL=$(grep "^CLOUDFLARE_TUNNEL_URL=" "$ENV_FILE" | cut -d'=' -f2 | sed 's|https://||' | sed 's|http://||' | tr -d '"' | tr -d "'" | tr -d ' ')

if [ -z "$TUNNEL_URL" ]; then
    echo -e "${RED}✗ CLOUDFLARE_TUNNEL_URL not found in .env file${NC}"
    exit 1
fi

# Get tunnel ID from existing config
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}✗ Config file not found at $CONFIG_FILE${NC}"
    exit 1
fi

TUNNEL_ID=$(grep "^tunnel:" "$CONFIG_FILE" | awk '{print $2}')

if [ -z "$TUNNEL_ID" ]; then
    echo -e "${RED}✗ Tunnel ID not found in config file${NC}"
    exit 1
fi

# Backup existing config
cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"

# Update config file
cat > "$CONFIG_FILE" <<EOF
tunnel: $TUNNEL_ID
credentials-file: /etc/cloudflared/credentials.json

ingress:
  - hostname: $TUNNEL_URL
    service: http://api_gateway:8000
  - service: http_status:404
EOF

echo -e "${GREEN}✓ Updated $CONFIG_FILE${NC}"
echo -e "${GREEN}  Domain: $TUNNEL_URL${NC}"
echo ""
echo "Restart Cloudflare tunnel to apply changes:"
echo "  docker compose restart cloudflared"








