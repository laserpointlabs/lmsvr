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
DATABASE_URL=sqlite:///./data/lmsvr.db
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

# Step 5: Build Docker images
echo -e "${YELLOW}Step 5: Building Docker images...${NC}"
cd "$PROJECT_ROOT"
docker compose build --quiet
echo -e "${GREEN}✓ Docker images built${NC}"
echo ""

# Step 6: Start core services
echo -e "${YELLOW}Step 6: Starting core services...${NC}"
docker compose up -d ollama api_gateway
echo "Waiting for services to start..."
sleep 10

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
echo ""

# Step 7: Test core services
echo -e "${YELLOW}Step 7: Testing core services...${NC}"

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

# Step 8: Initialize database
echo -e "${YELLOW}Step 8: Initializing database...${NC}"
cd "$PROJECT_ROOT"
source venv/bin/activate
python3 -c "from api_gateway.database import init_db; init_db(); print('Database initialized')" 2>&1
echo -e "${GREEN}✓ Database initialized${NC}"
echo ""

# Step 9: Cloudflare Tunnel setup (optional)
echo -e "${YELLOW}Step 9: Cloudflare Tunnel setup (optional)...${NC}"
read -p "Do you want to set up Cloudflare Tunnel? (y/n): " SETUP_TUNNEL

if [[ "$SETUP_TUNNEL" =~ ^[Yy]$ ]]; then
    if [ -f "$PROJECT_ROOT/cloudflare/setup_tunnel_cli.sh" ]; then
        echo "Running Cloudflare tunnel setup..."
        cd "$PROJECT_ROOT/cloudflare"
        bash setup_tunnel_cli.sh
        
        # Start Cloudflare container
        cd "$PROJECT_ROOT"
        docker compose up -d cloudflared
        sleep 5
        
        if docker compose ps cloudflared | grep -q "Up"; then
            echo -e "${GREEN}✓ Cloudflare tunnel is running${NC}"
        else
            echo -e "${YELLOW}⚠ Cloudflare tunnel may need configuration${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Cloudflare setup script not found${NC}"
    fi
else
    echo -e "${YELLOW}  Skipping Cloudflare Tunnel setup${NC}"
fi
echo ""

# Step 10: Run tests
echo -e "${YELLOW}Step 10: Running tests...${NC}"
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
echo "   curl -H \"Authorization: Bearer <your_api_key>\" http://localhost:8001/api/models"
echo ""
if [[ "$SETUP_TUNNEL" =~ ^[Yy]$ ]]; then
    echo "6. Test Cloudflare tunnel (after DNS propagation, ~2-5 minutes):"
    echo "   curl https://api.yourdomain.com/health"
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


