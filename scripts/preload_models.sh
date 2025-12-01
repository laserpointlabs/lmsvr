#!/bin/bash

# Script to preload/warmup Ollama models to avoid first-request latency
# Usage: OLLAMA_PRELOAD_MODELS="llama3.2:1b mistral" ./scripts/preload_models.sh

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
MODELS="${OLLAMA_PRELOAD_MODELS:-${OLLAMA_MODELS:-}}"

if [ -z "$MODELS" ]; then
    echo -e "${YELLOW}No models specified for preloading${NC}"
    echo "Set OLLAMA_PRELOAD_MODELS or OLLAMA_MODELS environment variable, e.g.:"
    echo "  OLLAMA_PRELOAD_MODELS=\"llama3.2:1b mistral codellama\""
    exit 0
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Ollama Model Preloader${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Ollama Host: $OLLAMA_HOST"
echo "Models to preload: $MODELS"
echo ""

# Wait for Ollama to be ready
echo -e "${YELLOW}Waiting for Ollama to be ready...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -sf "$OLLAMA_HOST/api/tags" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama is ready${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "  Waiting... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}✗ Ollama did not become ready in time${NC}"
    exit 1
fi

echo ""

# Preload each model
for model in $MODELS; do
    echo -e "${YELLOW}Preloading model: $model${NC}"
    
    # Check if model exists
    if ! curl -sf "$OLLAMA_HOST/api/tags" | grep -q "\"name\":\"$model\""; then
        echo -e "${YELLOW}  ⚠ Model $model not found, skipping${NC}"
        echo "  Make sure to pull it first: docker exec -it ollama ollama pull $model"
        continue
    fi
    
    # Make a warmup request to load the model
    echo -e "${YELLOW}  Loading model into memory/GPU...${NC}"
    START_TIME=$(date +%s)
    
    RESPONSE=$(curl -s -X POST "$OLLAMA_HOST/api/generate" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"$model\",
            \"prompt\": \"Hi\",
            \"stream\": false,
            \"options\": {
                \"num_predict\": 5,
                \"temperature\": 0.1
            }
        }" 2>&1)
    
    ELAPSED=$(($(date +%s) - START_TIME))
    
    if echo "$RESPONSE" | grep -q "\"response\""; then
        echo -e "${GREEN}  ✓ Model $model preloaded successfully (${ELAPSED}s)${NC}"
    else
        echo -e "${RED}  ✗ Failed to preload $model${NC}"
        echo "  Response: $RESPONSE"
    fi
    echo ""
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Model preload process completed${NC}"
echo -e "${GREEN}========================================${NC}"

