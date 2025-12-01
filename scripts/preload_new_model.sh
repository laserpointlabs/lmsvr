#!/bin/bash
# Quick script to pull and preload a new model

if [ -z "$1" ]; then
    echo "Usage: $0 <model_name>"
    echo "Example: $0 codellama"
    exit 1
fi

MODEL="$1"
OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"

echo "Pulling model: $MODEL"
docker exec -it ollama ollama pull "$MODEL"

echo ""
echo "Preloading model: $MODEL"
OLLAMA_PRELOAD_MODELS="$MODEL" python3 scripts/preload_models.py

