#!/bin/bash
# Entrypoint wrapper for Ollama that preloads models after startup

set -e

# Start Ollama server in the background
echo "Starting Ollama server..."
/usr/local/bin/ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama server to be ready..."
sleep 5

# Run the model loading script
if [ -f "/scripts/load_models.sh" ]; then
    echo "Running model preload script..."
    /scripts/load_models.sh || {
        echo "Warning: Model preload script failed, continuing anyway..."
    }
fi

# Wait for Ollama process (keep container running)
wait $OLLAMA_PID










