#!/bin/bash
# Script to preload Ollama models on container startup
# Reads OLLAMA_PRELOAD_MODELS environment variable (comma-separated list)

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Waiting for Ollama to be ready...${NC}"

# Wait for Ollama to be ready (max 60 seconds)
MAX_WAIT=60
WAIT_COUNT=0
while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if ollama list >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama is ready${NC}"
        break
    fi
    WAIT_COUNT=$((WAIT_COUNT + 1))
    if [ $WAIT_COUNT -eq $MAX_WAIT ]; then
        echo -e "${RED}✗ Ollama did not become ready in time${NC}"
        exit 1
    fi
    sleep 1
done

# Check if OLLAMA_PRELOAD_MODELS is set
if [ -z "$OLLAMA_PRELOAD_MODELS" ]; then
    echo -e "${YELLOW}No models specified in OLLAMA_PRELOAD_MODELS, skipping preload${NC}"
    exit 0
fi

echo -e "${YELLOW}Preloading models: $OLLAMA_PRELOAD_MODELS${NC}"

# Split comma-separated list and load each model
IFS=',' read -ra MODELS <<< "$OLLAMA_PRELOAD_MODELS"
for model in "${MODELS[@]}"; do
    # Trim whitespace
    model=$(echo "$model" | xargs)
    
    if [ -z "$model" ]; then
        continue
    fi
    
    echo -e "${YELLOW}Loading model: $model${NC}"
    
    # Check if model exists locally, if not pull it first
    if ! ollama list | grep -q "$model"; then
        echo -e "${YELLOW}  Model not found locally, pulling: $model${NC}"
        ollama pull "$model" || {
            echo -e "${RED}  ✗ Failed to pull model: $model${NC}"
            continue
        }
    fi
    
    # Load the model using API with keep_alive=-1
    echo -e "${YELLOW}  Warming up model: $model${NC}"
    # Use Python to make API call (Python is available in Ollama container)
    python3 -c "
import json
import urllib.request
import urllib.parse

data = json.dumps({
    'model': '$model',
    'prompt': 'test',
    'stream': False,
    'keep_alive': '-1'
}).encode('utf-8')

req = urllib.request.Request('http://localhost:11434/api/generate', data=data)
req.add_header('Content-Type', 'application/json')

try:
    with urllib.request.urlopen(req, timeout=300) as response:
        response.read()
    print('Success')
except Exception as e:
    print(f'Error: {e}')
    exit(1)
" >/dev/null 2>&1 && {
        echo -e "${GREEN}  ✓ Model loaded: $model${NC}"
    } || {
        echo -e "${RED}  ✗ Failed to load model: $model${NC}"
        continue
    }
done

echo -e "${GREEN}✓ Model preloading complete${NC}"

# Show loaded models
echo -e "${YELLOW}Currently loaded models:${NC}"
ollama ps
