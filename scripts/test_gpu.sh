#!/bin/bash

# GPU Access Test Script for Ollama
# This script verifies that GPU is accessible to the Ollama container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}GPU Access Test for Ollama${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if nvidia-smi is available (indicates NVIDIA drivers)
echo -e "${YELLOW}Step 1: Checking NVIDIA drivers...${NC}"
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ NVIDIA drivers detected${NC}"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader | head -1
    echo ""
else
    echo -e "${RED}✗ nvidia-smi not found${NC}"
    echo "  NVIDIA drivers may not be installed"
    echo "  GPU access will not be available"
    exit 1
fi

# Check if nvidia-container-toolkit is installed
echo -e "${YELLOW}Step 2: Checking NVIDIA Container Toolkit...${NC}"
if command -v nvidia-container-runtime &> /dev/null || docker info 2>/dev/null | grep -q nvidia; then
    echo -e "${GREEN}✓ NVIDIA Container Toolkit detected${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠ NVIDIA Container Toolkit not detected${NC}"
    echo "  Install with: sudo apt-get install -y nvidia-container-toolkit"
    echo "  Then restart Docker: sudo systemctl restart docker"
    echo ""
fi

# Check if Docker daemon supports GPU
echo -e "${YELLOW}Step 3: Checking Docker GPU support...${NC}"
if docker run --rm --gpus all nvidia/cuda:11.0.3-base-ubuntu20.04 nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ Docker can access GPU${NC}"
    echo ""
else
    echo -e "${RED}✗ Docker cannot access GPU${NC}"
    echo "  Check Docker daemon configuration"
    echo "  Ensure /etc/docker/daemon.json includes nvidia runtime"
    exit 1
fi

# Check if Ollama container is running
echo -e "${YELLOW}Step 4: Checking Ollama container status...${NC}"
if docker ps | grep -q ollama; then
    echo -e "${GREEN}✓ Ollama container is running${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠ Ollama container is not running${NC}"
    echo "  Starting Ollama container..."
    docker compose up -d ollama
    sleep 5
fi

# Test GPU access inside Ollama container
echo -e "${YELLOW}Step 5: Testing GPU access inside Ollama container...${NC}"
if docker exec ollama nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ GPU is accessible inside Ollama container${NC}"
    echo ""
    echo "GPU Information:"
    docker exec ollama nvidia-smi --query-gpu=index,name,memory.total,memory.used --format=csv,noheader
    echo ""
else
    echo -e "${RED}✗ GPU is NOT accessible inside Ollama container${NC}"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Ensure docker-compose.yml has GPU configuration"
    echo "2. Restart Docker: sudo systemctl restart docker"
    echo "3. Recreate containers: docker compose up -d --force-recreate ollama"
    exit 1
fi

# Test Ollama GPU detection
echo -e "${YELLOW}Step 6: Testing Ollama GPU detection...${NC}"
GPU_INFO=$(docker exec ollama ollama ps 2>&1 || echo "")
if echo "$GPU_INFO" | grep -qi "gpu\|cuda\|nvidia"; then
    echo -e "${GREEN}✓ Ollama detects GPU${NC}"
    echo ""
elif docker exec ollama ollama list &> /dev/null; then
    echo -e "${YELLOW}⚠ Ollama is running but GPU detection unclear${NC}"
    echo "  This may be normal if no models are loaded"
    echo ""
else
    echo -e "${RED}✗ Cannot communicate with Ollama${NC}"
    echo "  Check container logs: docker logs ollama"
    exit 1
fi

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}GPU Access Test Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "GPU is configured and accessible to Ollama."
echo "You can now pull and run models with GPU acceleration."
echo ""
echo "Example:"
echo "  docker exec -it ollama ollama pull llama3"
echo "  docker exec -it ollama ollama run llama3"

