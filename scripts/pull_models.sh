#!/bin/bash

# Script to pull Ollama models specified in environment variable
# Usage: OLLAMA_MODELS="llama3.2:1b mistral" ./scripts/pull_models.sh

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
MODELS="${OLLAMA_MODELS:-}"

if [ -z "$MODELS" ]; then
    echo -e "${YELLOW}No models specified in OLLAMA_MODELS environment variable${NC}"
    echo "Set OLLAMA_MODELS to pull models automatically, e.g.:"
    echo "  OLLAMA_MODELS=\"llama3.2:1b mistral codellama\""
    exit 0
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Ollama Model Puller${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Ollama Host: $OLLAMA_HOST"
echo "Models to pull: $MODELS"
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

# Pull each model
for model in $MODELS; do
    echo -e "${YELLOW}Pulling model: $model${NC}"
    
    # Check if model already exists
    if curl -sf "$OLLAMA_HOST/api/tags" | grep -q "\"name\":\"$model\""; then
        echo -e "${GREEN}  ✓ Model $model already exists, skipping${NC}"
    else
        # Pull the model (Ollama pull is async, so we trigger it and wait)
        echo -e "${YELLOW}  Starting pull for $model...${NC}"
        PULL_OUTPUT=$(curl -sf -X POST "$OLLAMA_HOST/api/pull" \
            -H "Content-Type: application/json" \
            -d "{\"name\":\"$model\"}" 2>&1)
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}  ✓ Pull request sent for $model${NC}"
            
            # Wait and check if model appears (simplified - actual pull may take longer)
            echo -e "${YELLOW}  Waiting for $model to finish downloading...${NC}"
            MAX_WAIT=300  # 5 minutes max per model
            WAITED=0
            
            while [ $WAITED -lt $MAX_WAIT ]; do
                if curl -sf "$OLLAMA_HOST/api/tags" | grep -q "\"name\":\"$model\""; then
                    echo -e "${GREEN}  ✓ Model $model downloaded successfully${NC}"
                    break
                fi
                sleep 5
                WAITED=$((WAITED + 5))
                if [ $((WAITED % 30)) -eq 0 ]; then
                    echo "  Still downloading... (${WAITED}s)"
                fi
            done
            
            if [ $WAITED -ge $MAX_WAIT ]; then
                echo -e "${YELLOW}  ⚠ Pull may still be in progress (timeout reached)${NC}"
            fi
        else
            echo -e "${RED}  ✗ Failed to start pull for $model${NC}"
            echo "  Error: $PULL_OUTPUT"
        fi
    fi
    echo ""
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Model pull process completed${NC}"
echo -e "${GREEN}========================================${NC}"

# List available models
echo ""
echo -e "${BLUE}Available models:${NC}"
curl -s "$OLLAMA_HOST/api/tags" | python3 -m json.tool 2>/dev/null | grep -E '"name"|"size"' || echo "Could not list models"

