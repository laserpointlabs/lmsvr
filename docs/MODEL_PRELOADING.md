# Model Preloading Guide

This guide explains how to automatically preload Ollama models on container startup and keep them loaded permanently in GPU memory.

## Overview

The Ollama API Gateway includes an automatic model preloading system that:
- Loads specified models into GPU memory on container startup
- Keeps models loaded permanently (no 5-minute timeout)
- Automatically pulls missing models
- Distributes models across multiple GPUs efficiently
- **Automatically handles both regular and embedding models** (uses correct API endpoint for each type)

## Configuration

### Environment Variables

Configure model preloading via environment variables in your `.env` file:

```bash
# Comma-separated list of models to preload on startup
OLLAMA_PRELOAD_MODELS="qwen3-coder:30b,devstral,qwen2.5-coder:1.5b-base,nomic-embed-text"

# Keep models loaded forever (negative value = forever)
OLLAMA_KEEP_ALIVE=-1

# Maximum number of models to keep loaded simultaneously
# Default: 6 (for 4 GPUs with 16GB each)
OLLAMA_MAX_LOADED_MODELS=6
```

### Example Configurations

**Minimal Setup (2-3 models):**
```bash
OLLAMA_PRELOAD_MODELS="qwen3-coder:30b,qwen2.5-coder:1.5b-base"
OLLAMA_MAX_LOADED_MODELS=3
```

**Recommended Setup (4 models for Continue.dev):**
```bash
OLLAMA_PRELOAD_MODELS="qwen3-coder:30b,devstral,qwen2.5-coder:1.5b-base,nomic-embed-text"
OLLAMA_MAX_LOADED_MODELS=6
```

**Maximum Performance (All models):**
```bash
OLLAMA_PRELOAD_MODELS="qwen3-coder:30b,devstral,gpt-oss:20b,qwen2.5-coder:7b-base,nomic-embed-text"
OLLAMA_MAX_LOADED_MODELS=8
```

## How It Works

### Startup Process

1. **Container Starts**: Docker Compose runs `scripts/ollama-start.sh` as the entrypoint
2. **Ollama Server Starts**: Script starts `ollama serve` in the background
3. **Wait for Ready**: Script waits for Ollama API to be responsive
4. **Read Configuration**: Script reads `OLLAMA_PRELOAD_MODELS` from environment
5. **Load Models**: For each model:
   - Verify model exists locally
   - Pull model if missing
   - Load model into GPU memory:
     - Regular models: Use `ollama run` (generate API)
     - Embedding models: Use `/api/embeddings` endpoint (automatically detected)
   - Keep model loaded permanently

### Model Loading Details

**Regular Models** (chat, code generation):
- Loaded via `ollama run` command
- Appear in `ollama ps` output
- Show "Forever" in UNTIL column
- Stay loaded in GPU memory permanently

**Embedding Models**:
- **Important**: Embedding models cannot be loaded via `ollama run` (they don't support the generate API)
- Must be loaded via the `/api/embeddings` endpoint
- The startup script automatically detects embedding models and uses the correct API
- Once loaded via embeddings API, they appear in `ollama ps` with "Forever" status
- Stay loaded in GPU memory permanently (just like regular models)
- **Note**: This is not a container rebuild issue - embedding models require a different API endpoint than regular models

### GPU Memory Distribution

Ollama automatically distributes models across available GPUs:
- Models are split across GPUs based on available memory
- Each GPU can hold multiple models
- Models are balanced for optimal performance

## Verification

### Check Loaded Models

```bash
# List currently loaded models
docker exec ollama ollama ps

# Expected output:
# NAME               ID              SIZE     PROCESSOR    CONTEXT    UNTIL   
# qwen3-coder:30b    ...             19 GB   100% GPU     4096       Forever
# devstral           ...             15 GB   100% GPU     4096       Forever
```

### Check GPU Memory Usage

```bash
# View GPU memory usage
docker exec ollama nvidia-smi

# Or get summary
docker exec ollama nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv
```

### Check Container Logs

```bash
# View preloading progress
docker compose logs ollama | grep -E "(Preloading|Loading|loaded|complete|✓)"

# View full startup logs
docker compose logs ollama --tail 100
```

## Troubleshooting

### Models Not Loading

**Symptoms:** Models don't appear in `ollama ps` after container restart

**Solutions:**
1. Check `OLLAMA_PRELOAD_MODELS` is set in `.env` file
2. Verify models are pulled: `docker exec ollama ollama list`
3. Check container logs: `docker compose logs ollama`
4. Ensure `OLLAMA_KEEP_ALIVE=-1` is set

### Embedding Models Not Loading

**Symptoms:** Embedding models (like `nomic-embed-text`) don't appear in `ollama ps` after restart

**Important Note:** This is **not** a container rebuild issue. Embedding models require the `/api/embeddings` endpoint, not the `/api/generate` endpoint used by regular models.

**Solutions:**
1. The startup script automatically handles embedding models via the embeddings API
2. Check logs for "✓ Model loaded: [model] (embedding)" message
3. Verify the embeddings API call succeeded: Look for `200` status in logs
4. If still not loading, manually trigger: The script uses `/dev/tcp` to call the embeddings API - check logs for any errors
5. Embedding models will appear in `ollama ps` once successfully loaded via the embeddings API

### Models Unloading After 5 Minutes

**Symptoms:** Models disappear from `ollama ps` after inactivity

**Solutions:**
1. Verify `OLLAMA_KEEP_ALIVE=-1` in docker-compose.yml
2. Check environment variable is being passed: `docker exec ollama env | grep KEEP_ALIVE`
3. Restart container: `docker compose restart ollama`

### Out of Memory Errors

**Symptoms:** Container crashes or models fail to load

**Solutions:**
1. Reduce number of models in `OLLAMA_PRELOAD_MODELS`
2. Use smaller/quantized models
3. Increase `OLLAMA_MAX_LOADED_MODELS` if you have more VRAM
4. Check GPU memory: `docker exec ollama nvidia-smi`

### Script Not Running

**Symptoms:** No preloading messages in logs

**Solutions:**
1. Verify script is executable: `ls -l scripts/ollama-start.sh`
2. Check docker-compose.yml has correct entrypoint
3. Ensure script is mounted: Check volumes in docker-compose.yml
4. Check script syntax: `bash -n scripts/ollama-start.sh`

## Best Practices

### Model Selection

- **Start Small**: Begin with 2-3 models, add more as needed
- **Consider Size**: Larger models (30B+) consume significant VRAM
- **Balance Types**: Mix chat, code, and embedding models based on use case

### Resource Management

- **Monitor Usage**: Regularly check GPU memory with `nvidia-smi`
- **Adjust Limits**: Tune `OLLAMA_MAX_LOADED_MODELS` based on your hardware
- **Plan Capacity**: Ensure total model sizes fit within available VRAM

### Performance Optimization

- **Preload Frequently Used Models**: Only preload models you use regularly
- **Use Quantized Models**: Smaller models load faster and use less memory
- **Distribute Load**: Spread models across multiple GPUs for better performance

## Advanced Configuration

### Custom Startup Script

To customize the preloading behavior, modify `scripts/ollama-start.sh`:

```bash
# Edit the script
nano scripts/ollama-start.sh

# Make it executable
chmod +x scripts/ollama-start.sh

# Restart container
docker compose restart ollama
```

### Manual Model Loading

To manually load models without restarting:

```bash
# Load a specific model
docker exec ollama ollama run qwen3-coder:30b "test"

# Check if it's loaded
docker exec ollama ollama ps
```

### Disable Preloading

To disable automatic preloading:

```bash
# In .env file, set empty or remove the variable
OLLAMA_PRELOAD_MODELS=""

# Or comment it out
# OLLAMA_PRELOAD_MODELS="model1,model2"
```

## Related Documentation

- [Continue.dev Setup Guide](CONTINUE_DEV_SETUP.md) - Recommended models for Continue.dev
- [GPU Testing Guide](../docs/GPU_TESTING.md) - Verify GPU is working correctly
- [README.md](../README.md) - Main project documentation


