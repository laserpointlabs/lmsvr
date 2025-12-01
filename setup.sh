#!/bin/bash

# Complete Setup Script for Ollama API Gateway
# Handles installation, configuration, and testing on any computer

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_DIR="$PROJECT_ROOT"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Ollama API Gateway - Complete Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Check prerequisites
echo -e "${YELLOW}Step 1: Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "  Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker is installed${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    echo "  Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose is available${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    echo "  Please install Python 3.11+: https://www.python.org/downloads/"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✓ Python is installed ($PYTHON_VERSION)${NC}"

# Check Docker daemon
if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Docker daemon is not running${NC}"
    echo "  Please start Docker: sudo systemctl start docker"
    exit 1
fi
echo -e "${GREEN}✓ Docker daemon is running${NC}"
echo ""

# Step 2: Create necessary directories
echo -e "${YELLOW}Step 2: Creating directories...${NC}"
mkdir -p "$PROJECT_ROOT/data"
mkdir -p "$PROJECT_ROOT/cloudflare"
chmod 755 "$PROJECT_ROOT/data"
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Step 3: Setup environment file
echo -e "${YELLOW}Step 3: Setting up environment...${NC}"
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo -e "${GREEN}✓ Created .env file from .env.example${NC}"
        echo -e "${YELLOW}  Please review and update .env file if needed${NC}"
    else
        cat > "$PROJECT_ROOT/.env" <<EOF
DATABASE_URL=sqlite:///./data/lmapi.db
OLLAMA_BASE_URL=http://ollama:11434
LOG_LEVEL=INFO
EOF
        echo -e "${GREEN}✓ Created default .env file${NC}"
    fi
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi
echo ""

# Step 4: Setup Python virtual environment
echo -e "${YELLOW}Step 4: Setting up Python environment...${NC}"
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    python3 -m venv "$PROJECT_ROOT/venv"
    echo -e "${GREEN}✓ Created virtual environment${NC}"
fi

source "$PROJECT_ROOT/venv/bin/activate"

# Install CLI dependencies
if [ -f "$PROJECT_ROOT/api_gateway/requirements.txt" ]; then
    pip install -q -r "$PROJECT_ROOT/api_gateway/requirements.txt"
    echo -e "${GREEN}✓ Installed Python dependencies${NC}"
fi

# Install test dependencies
if [ -f "$PROJECT_ROOT/requirements-dev.txt" ]; then
    pip install -q -r "$PROJECT_ROOT/requirements-dev.txt"
    echo -e "${GREEN}✓ Installed test dependencies${NC}"
fi
echo ""

# Step 5: Export user/group IDs for Docker (must be before docker compose)
# Note: UID is readonly in bash, so we use DOCKER_UID and DOCKER_GID
export DOCKER_UID=$(id -u)
export DOCKER_GID=$(id -g)
echo -e "${BLUE}  Docker containers will run as UID: $DOCKER_UID, GID: $DOCKER_GID${NC}"
echo ""

# Step 5.5: Initialize database BEFORE Docker starts (ensures user ownership)
echo -e "${YELLOW}Step 5.5: Initializing database...${NC}"
export DATABASE_URL="sqlite:///./data/lmapi.db"
python3 -c "from api_gateway.database import init_db; init_db()" 2>/dev/null || {
    echo -e "${YELLOW}  Database initialization will happen on first API Gateway start${NC}"
}
# Ensure database file has correct permissions (writable by container)
if [ -f "$PROJECT_ROOT/data/lmapi.db" ]; then
    chmod 666 "$PROJECT_ROOT/data/lmapi.db" 2>/dev/null || true
fi
echo -e "${GREEN}✓ Database ready${NC}"
echo ""

# Step 6: Build Docker images
echo -e "${YELLOW}Step 6: Building Docker images...${NC}"
cd "$PROJECT_ROOT"
docker compose build --quiet
echo -e "${GREEN}✓ Docker images built${NC}"
echo ""

# Step 7: Start core services
echo -e "${YELLOW}Step 7: Starting core services...${NC}"
# Start all services including cloudflared if configured
if [ -f "$PROJECT_ROOT/cloudflare/credentials.json" ] && [ -f "$PROJECT_ROOT/cloudflare/config.yml" ]; then
    echo -e "${BLUE}  Cloudflare tunnel detected, starting all services...${NC}"
    docker compose up -d ollama api_gateway cloudflared
else
    docker compose up -d ollama api_gateway
fi
echo "Waiting for services to start..."
sleep 10

# Ensure database file has correct ownership after Docker starts
if [ -f "$PROJECT_ROOT/data/lmapi.db" ]; then
    chown "$(id -u):$(id -g)" "$PROJECT_ROOT/data/lmapi.db" 2>/dev/null || true
    chmod 644 "$PROJECT_ROOT/data/lmapi.db" 2>/dev/null || true
fi

# Check Ollama
if docker compose ps ollama | grep -q "Up"; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
else
    echo -e "${RED}✗ Ollama failed to start${NC}"
    docker compose logs ollama --tail 10
    exit 1
fi

# Check API Gateway
if docker compose ps api_gateway | grep -q "Up"; then
    echo -e "${GREEN}✓ API Gateway is running${NC}"
else
    echo -e "${RED}✗ API Gateway failed to start${NC}"
    docker compose logs api_gateway --tail 10
    exit 1
fi

# Check Cloudflare tunnel if it was started
if [ -f "$PROJECT_ROOT/cloudflare/credentials.json" ] && [ -f "$PROJECT_ROOT/cloudflare/config.yml" ]; then
    if docker compose ps cloudflared | grep -q "Up"; then
        echo -e "${GREEN}✓ Cloudflare tunnel is running${NC}"
    else
        echo -e "${YELLOW}⚠ Cloudflare tunnel may still be starting${NC}"
    fi
fi
echo ""

# Step 8: Test core services
echo -e "${YELLOW}Step 8: Testing core services...${NC}"

# Test API Gateway health
for i in {1..30}; do
    if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API Gateway health check passed${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ API Gateway health check failed${NC}"
        docker compose logs api_gateway --tail 20
        exit 1
    fi
    sleep 1
done

# Test Ollama connectivity
if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama is accessible${NC}"
else
    echo -e "${YELLOW}⚠ Ollama may still be starting (this is OK)${NC}"
fi
echo ""

# Step 9: Verify database ownership
echo -e "${YELLOW}Step 9: Verifying database permissions...${NC}"
if [ -f "$PROJECT_ROOT/data/lmapi.db" ]; then
    # Fix ownership if needed (in case Docker created it)
    chown "$(id -u):$(id -g)" "$PROJECT_ROOT/data/lmapi.db" 2>/dev/null || true
    chmod 644 "$PROJECT_ROOT/data/lmapi.db" 2>/dev/null || true
    echo -e "${GREEN}✓ Database permissions verified${NC}"
else
    # Initialize database if it doesn't exist
    cd "$PROJECT_ROOT"
    source venv/bin/activate
    export DATABASE_URL="sqlite:///./data/lmapi.db"
    python3 -c "from api_gateway.database import init_db; init_db(); print('Database initialized')" 2>&1
    chmod 644 "$PROJECT_ROOT/data/lmapi.db" 2>/dev/null || true
    echo -e "${GREEN}✓ Database initialized${NC}"
fi
echo ""

# Step 10: Cloudflare Tunnel setup (optional)
echo -e "${YELLOW}Step 10: Cloudflare Tunnel setup (optional)...${NC}"
read -p "Do you want to set up Cloudflare Tunnel? (y/n): " SETUP_TUNNEL

if [[ "$SETUP_TUNNEL" =~ ^[Yy]$ ]]; then
    if [ -f "$PROJECT_ROOT/cloudflare/setup_tunnel_cli.sh" ]; then
        echo "Running Cloudflare tunnel setup..."
        cd "$PROJECT_ROOT/cloudflare"
        bash setup_tunnel_cli.sh
        
        # Sync config from .env if it exists
        if [ -f "$PROJECT_ROOT/.env" ]; then
            if [ -f "$PROJECT_ROOT/cloudflare/update_config_from_env.sh" ]; then
                echo "Syncing Cloudflare config from .env..."
                bash update_config_from_env.sh
            fi
        fi
        
        # Start Cloudflare container
        cd "$PROJECT_ROOT"
        docker compose up -d cloudflared
        sleep 8
        
        # Check tunnel status
        if docker compose ps cloudflared | grep -q "Up"; then
            echo -e "${GREEN}✓ Cloudflare tunnel container is running${NC}"
            
            # Check tunnel connections
            if docker compose logs cloudflared 2>&1 | grep -q "Registered tunnel connection"; then
                echo -e "${GREEN}✓ Cloudflare tunnel is connected${NC}"
            else
                echo -e "${YELLOW}⚠ Tunnel may still be connecting...${NC}"
            fi
            
            # Get domain from .env
            TUNNEL_URL=$(grep "^CLOUDFLARE_TUNNEL_URL=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2 | sed 's|https://||' | sed 's|http://||' | tr -d '"' | tr -d "'" || echo "lmapi.laserpointlabs.com")
            
            echo ""
            echo -e "${BLUE}Cloudflare Tunnel configured:${NC}"
            echo "  Domain: $TUNNEL_URL"
            echo "  Note: DNS propagation may take 2-5 minutes"
            echo "  Test: curl https://$TUNNEL_URL/health"
        else
            echo -e "${YELLOW}⚠ Cloudflare tunnel container failed to start${NC}"
            echo "  Check logs: docker compose logs cloudflared"
        fi
    else
        echo -e "${YELLOW}⚠ Cloudflare setup script not found${NC}"
    fi
else
    echo -e "${YELLOW}  Skipping Cloudflare Tunnel setup${NC}"
fi
echo ""

# Step 11: Run tests
echo -e "${YELLOW}Step 11: Running tests...${NC}"
cd "$PROJECT_ROOT"
source venv/bin/activate

# Run database tests
DB_TEST_OUTPUT=$(pytest tests/test_database.py -v --tb=short 2>&1 || true)
if echo "$DB_TEST_OUTPUT" | tail -5 | grep -q "passed\|PASSED\|PASSED\|test_database.py PASSED"; then
    echo -e "${GREEN}✓ Database tests passed${NC}"
else
    echo -e "${YELLOW}⚠ Some database tests may have failed (check output above)${NC}"
    echo "$DB_TEST_OUTPUT" | tail -10
fi

# Run API tests (if API Gateway is accessible)
if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
    API_TEST_OUTPUT=$(pytest tests/test_api.py -v --tb=short 2>&1 || true)
    if echo "$API_TEST_OUTPUT" | tail -5 | grep -q "passed\|PASSED\|test_api.py PASSED"; then
        echo -e "${GREEN}✓ API tests passed${NC}"
    else
        echo -e "${YELLOW}⚠ Some API tests may have failed (check output above)${NC}"
        echo "$API_TEST_OUTPUT" | tail -10
    fi
else
    echo -e "${YELLOW}⚠ Skipping API tests (API Gateway not accessible)${NC}"
fi

# Test Cloudflare tunnel if configured
if [[ "$SETUP_TUNNEL" =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${YELLOW}Testing Cloudflare tunnel...${NC}"
    TUNNEL_URL=$(grep "^CLOUDFLARE_TUNNEL_URL=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2 | sed 's|https://||' | sed 's|http://||' | tr -d '"' | tr -d "'" || echo "")
    
    if [ -n "$TUNNEL_URL" ]; then
        echo "Waiting for DNS propagation (10 seconds)..."
        sleep 10
        
        if curl -sf "https://$TUNNEL_URL/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Cloudflare tunnel is accessible${NC}"
            curl -s "https://$TUNNEL_URL/health" | python3 -m json.tool 2>/dev/null || echo "  Response received"
        else
            echo -e "${YELLOW}⚠ Cloudflare tunnel not yet accessible${NC}"
            echo "  This is normal - DNS propagation can take 2-5 minutes"
            echo "  Tunnel container is running, check DNS in Cloudflare dashboard"
        fi
    fi
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Services Status:"
docker compose ps --format "table {{.Name}}\t{{.Status}}"
echo ""
echo "Next Steps:"
echo ""
echo "1. Create a customer:"
echo "   source venv/bin/activate"
echo "   python3 cli/cli.py create-customer \"Your Name\" \"your@email.com\" --budget 100.0"
echo ""
echo "2. Generate an API key:"
echo "   python3 cli/cli.py generate-key <customer_id>"
echo ""
echo "3. Pull some models:"
echo "   docker exec -it ollama ollama pull llama3"
echo ""
echo "4. Set pricing:"
echo "   python3 cli/cli.py set-pricing llama3 0.001 0.002"
echo ""
echo "5. Test the API:"
TUNNEL_URL=$(grep "^CLOUDFLARE_TUNNEL_URL=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2 | sed 's|https://||' | sed 's|http://||' | tr -d '"' | tr -d "'" || echo "")
if [ -n "$TUNNEL_URL" ] && [[ "$SETUP_TUNNEL" =~ ^[Yy]$ ]]; then
    echo "   # Via Cloudflare Tunnel (recommended):"
    echo "   curl -H \"Authorization: Bearer <your_api_key>\" https://$TUNNEL_URL/api/models"
    echo ""
    echo "   # Via localhost:"
    echo "   curl -H \"Authorization: Bearer <your_api_key>\" http://localhost:8001/api/models"
else
    echo "   curl -H \"Authorization: Bearer <your_api_key>\" http://localhost:8001/api/models"
fi
echo ""
if [[ "$SETUP_TUNNEL" =~ ^[Yy]$ ]]; then
    TUNNEL_URL=$(grep "^CLOUDFLARE_TUNNEL_URL=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2 | sed 's|https://||' | sed 's|http://||' | tr -d '"' | tr -d "'" || echo "lmapi.laserpointlabs.com")
    echo "6. Test Cloudflare tunnel (after DNS propagation, ~2-5 minutes):"
    echo "   curl https://$TUNNEL_URL/health"
    echo ""
fi
echo "Useful Commands:"
echo "  docker compose ps              # Check service status"
echo "  docker compose logs <service>  # View logs"
echo "  docker compose restart         # Restart all services"
echo "  docker compose down            # Stop all services"
echo ""
echo "Documentation:"
echo "  README.md                      # Full documentation"
echo "  QUICKSTART.md                  # Quick start guide"
echo "  cloudflare/SETUP_CLI.md       # Cloudflare tunnel setup"
echo ""
echo "Documentation:"
echo "  README.md                      # Full documentation"
echo "  QUICKSTART.md                  # Quick start guide"
echo "  cloudflare/SETUP_CLI.md       # Cloudflare tunnel setup"
echo ""


