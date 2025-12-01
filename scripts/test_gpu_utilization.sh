#!/bin/bash

# Test GPU Utilization for Ollama
# This script verifies that Ollama is actually using the GPU during inference

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}GPU Utilization Test for Ollama${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if nvidia-smi is available
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${RED}✗ nvidia-smi not found${NC}"
    echo "  NVIDIA drivers may not be installed"
    exit 1
fi
echo -e "${GREEN}✓ nvidia-smi available${NC}"

# Check if Ollama container is running
if ! docker ps | grep -q ollama; then
    echo -e "${RED}✗ Ollama container is not running${NC}"
    echo "  Start it with: docker compose up -d ollama"
    exit 1
fi
echo -e "${GREEN}✓ Ollama container is running${NC}"

# Check GPU availability in container
echo ""
echo -e "${YELLOW}Checking GPU access in container...${NC}"
if docker exec ollama nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ GPU accessible in container${NC}"
    docker exec ollama nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
else
    echo -e "${RED}✗ GPU not accessible in container${NC}"
    echo "  Check Docker GPU configuration"
    exit 1
fi

# Check if Ollama detects GPU
echo ""
echo -e "${YELLOW}Checking Ollama GPU detection...${NC}"
OLLAMA_GPU_INFO=$(docker exec ollama ollama show --modelfile 2>&1 || echo "")
if docker exec ollama ollama ps 2>&1 | grep -q "error\|Error"; then
    echo -e "${YELLOW}⚠ Could not check Ollama GPU status directly${NC}"
else
    echo -e "${GREEN}✓ Ollama is running${NC}"
fi

# Get a small model for testing (or use existing)
echo ""
echo -e "${YELLOW}Checking for available models...${NC}"
MODELS=$(docker exec ollama ollama list 2>/dev/null | tail -n +2 | awk '{print $1}' | head -1 || echo "")
if [ -z "$MODELS" ]; then
    echo -e "${YELLOW}⚠ No models found. Pulling a small test model...${NC}"
    echo "  This may take a few minutes..."
    docker exec ollama ollama pull llama3.2:1b 2>&1 | tail -5
    TEST_MODEL="llama3.2:1b"
else
    TEST_MODEL=$(echo "$MODELS" | head -1)
    echo -e "${GREEN}✓ Using model: $TEST_MODEL${NC}"
fi

# Monitor GPU utilization during inference
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Testing GPU Utilization${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Baseline GPU usage (before inference):${NC}"
BASELINE_UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | head -1)
BASELINE_MEM=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
echo "  GPU Utilization: ${BASELINE_UTIL}%"
echo "  Memory Used: ${BASELINE_MEM} MB"
echo ""

echo -e "${YELLOW}Starting inference test (this will take ~30 seconds)...${NC}"
echo -e "${YELLOW}Monitoring GPU utilization...${NC}"
echo ""

# Start GPU monitoring in background
(
    for i in {1..30}; do
        UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | head -1)
        MEM=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
        TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits | head -1)
        echo "[$i/30] GPU: ${UTIL}% | Memory: ${MEM} MB | Temp: ${TEMP}°C"
        sleep 1
    done
) &
MONITOR_PID=$!

# Run inference
INFERENCE_START=$(date +%s)
docker exec ollama ollama run "$TEST_MODEL" "Write a short story about a robot learning to paint. Make it exactly 100 words." > /dev/null 2>&1
INFERENCE_END=$(date +%s)
INFERENCE_TIME=$((INFERENCE_END - INFERENCE_START))

# Wait for monitor to finish
wait $MONITOR_PID 2>/dev/null || true

# Get final GPU stats
echo ""
echo -e "${YELLOW}Final GPU usage (after inference):${NC}"
FINAL_UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | head -1)
FINAL_MEM=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
echo "  GPU Utilization: ${FINAL_UTIL}%"
echo "  Memory Used: ${FINAL_MEM} MB"
echo ""

# Calculate GPU utilization increase
UTIL_INCREASE=$((FINAL_UTIL - BASELINE_UTIL))
MEM_INCREASE=$((FINAL_MEM - BASELINE_MEM))

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Results${NC}"
echo -e "${BLUE}========================================${NC}"
echo "  Inference Time: ${INFERENCE_TIME} seconds"
echo "  GPU Utilization Increase: ${UTIL_INCREASE}%"
echo "  Memory Increase: ${MEM_INCREASE} MB"
echo ""

# Determine if GPU was used
if [ "$UTIL_INCREASE" -gt 10 ] || [ "$MEM_INCREASE" -gt 50 ]; then
    echo -e "${GREEN}✓ GPU IS BEING UTILIZED${NC}"
    echo "  GPU usage increased significantly during inference"
    echo "  This indicates Ollama is using the GPU"
    exit 0
elif [ "$UTIL_INCREASE" -gt 0 ] || [ "$MEM_INCREASE" -gt 0 ]; then
    echo -e "${YELLOW}⚠ GPU usage detected but may be minimal${NC}"
    echo "  GPU utilization: ${UTIL_INCREASE}% increase"
    echo "  Memory increase: ${MEM_INCREASE} MB"
    echo "  This may indicate GPU is being used, but check model size"
    exit 0
else
    echo -e "${RED}✗ GPU DOES NOT APPEAR TO BE UTILIZED${NC}"
    echo "  No significant GPU usage detected during inference"
    echo "  Ollama may be using CPU instead"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check Docker GPU configuration:"
    echo "     docker exec ollama nvidia-smi"
    echo "  2. Verify NVIDIA Container Toolkit is installed"
    echo "  3. Check docker-compose.yml GPU settings"
    echo "  4. Restart Docker: sudo systemctl restart docker"
    exit 1
fi

