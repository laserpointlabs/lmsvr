#!/bin/bash

# Start the Ollama service in the background
ollama serve &

# Wait for Ollama service to be ready
echo "Waiting for Ollama to be ready..."
until ollama list >/dev/null 2>&1; do
  sleep 1
done

echo "Ollama is ready!"

# Check if OLLAMA_PRELOAD_MODELS is set
if [ -z "$OLLAMA_PRELOAD_MODELS" ]; then
    echo "No models specified in OLLAMA_PRELOAD_MODELS, skipping preload"
    wait -n
    exit 0
fi

echo "Preloading models: $OLLAMA_PRELOAD_MODELS"

# Split comma-separated list and preload each model
IFS=',' read -ra MODELS <<< "$OLLAMA_PRELOAD_MODELS"
for model in "${MODELS[@]}"; do
    # Trim whitespace
    model=$(echo "$model" | xargs)
    
    if [ -z "$model" ]; then
        continue
    fi
    
    echo "Preloading model: $model"
    
    # Check if model exists locally, if not pull it first
    if ! ollama list | grep -q "$model"; then
        echo "  Model not found locally, pulling: $model"
        ollama pull "$model" || {
            echo "  ✗ Failed to pull model: $model"
            continue
        }
    fi
    
    # Preload the model - try ollama run first (works for most models)
    # The OLLAMA_KEEP_ALIVE=-1 env var will keep it loaded
    echo "  Warming up model: $model"
    
    # Try ollama run - if it fails, the model might be an embedding model
    if echo "test" | timeout 30 ollama run "$model" >/dev/null 2>&1; then
        echo "  ✓ Model loaded: $model"
    else
        # If ollama run fails, try embeddings API for embedding models
        # Use a simpler approach: create a temp script to call the API properly
        if timeout 30 bash -c "
json='{\"model\":\"$model\",\"prompt\":\"test\"}'
len=\$(echo -n \"\$json\" | wc -c)
exec 3<>/dev/tcp/localhost/11434
printf \"POST /api/embeddings HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: \$len\r\n\r\n\$json\" >&3
sleep 2
response=\$(cat <&3 2>/dev/null)
echo \"\$response\" | head -1 | grep -q \"200\"
" 2>/dev/null; then
            echo "  ✓ Model loaded: $model (embedding)"
        elif ollama show "$model" >/dev/null 2>&1; then
            echo "  ✓ Model available: $model (will load on first use)"
        else
            echo "  ✗ Failed to load model: $model"
            continue
        fi
    fi
done

echo "Model preloading complete!"
echo "Currently loaded models:"
ollama ps

# Keep the container running
wait -n
