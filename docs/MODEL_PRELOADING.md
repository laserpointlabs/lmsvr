# Model Preloading Guide

This guide explains how to preload/warmup Ollama models to avoid first-request latency.

## Problem

When you pull a model with Ollama, it downloads the model files to disk. However, the model still needs to be loaded into memory (and GPU if available) on the first request, which can take several seconds to minutes depending on model size and hardware.

## Solution

Preloading models makes a warmup request to each model, loading it into memory/GPU before the first real request. This eliminates the cold-start delay.

---

## Methods

### Method 1: Automatic Preloading (Docker Compose)

The easiest way is to use the `model_preloader` service in docker-compose.yml:

**1. Set environment variable:**
```bash
# In your .env file or export before docker compose up
export OLLAMA_PRELOAD_MODELS="llama3.2:1b mistral codellama"
```

**2. Start services:**
```bash
docker compose up -d
```

The `model_preloader` service will:
- Wait for models to be pulled
- Make warmup requests to each model
- Load models into memory/GPU
- Exit when complete

**Note:** You can use `OLLAMA_PRELOAD_MODELS` to specify different models for preloading than pulling, or use `OLLAMA_MODELS` for both.

### Method 2: Manual Preloading Script

**Python script:**
```bash
# Preload specific models
OLLAMA_PRELOAD_MODELS="llama3.2:1b mistral" python3 scripts/preload_models.py

# Or use OLLAMA_MODELS
OLLAMA_MODELS="llama3.2:1b mistral" python3 scripts/preload_models.py
```

**Bash script:**
```bash
# Preload specific models
OLLAMA_PRELOAD_MODELS="llama3.2:1b mistral" ./scripts/preload_models.sh
```

### Method 3: Direct Ollama Command

You can also preload models directly using Ollama's API:

```bash
# Make a warmup request
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "prompt": "Hi",
    "stream": false,
    "options": {
      "num_predict": 5,
      "temperature": 0.1
    }
  }'
```

Or using the Ollama CLI:
```bash
docker exec -it ollama ollama run llama3.2:1b "Hi"
```

---

## Configuration

### Environment Variables

- `OLLAMA_PRELOAD_MODELS` - Space-separated list of models to preload
- `OLLAMA_MODELS` - If `OLLAMA_PRELOAD_MODELS` is not set, this will be used
- `OLLAMA_HOST` - Ollama service URL (default: `http://localhost:11434`)

### Docker Compose

The `model_preloader` service runs automatically after `model_puller` completes:

```yaml
model_preloader:
  depends_on:
    model_puller:
      condition: service_completed_successfully
    ollama:
      condition: service_started
```

---

## How It Works

1. **Pull Phase** (`model_puller`):
   - Downloads model files to disk
   - Models are available but not loaded

2. **Preload Phase** (`model_preloader`):
   - Makes a minimal warmup request to each model
   - Model loads into memory/GPU
   - Subsequent requests are instant

3. **Warmup Request**:
   - Uses a very short prompt ("Hi")
   - Requests only 5 tokens (`num_predict: 5`)
   - Minimal cost/time overhead

---

## Example Workflow

**Complete setup with preloading:**
```bash
# 1. Set models to pull and preload
export OLLAMA_MODELS="llama3.2:1b mistral"

# 2. Start services (pulls and preloads automatically)
docker compose up -d

# 3. Check logs
docker compose logs model_preloader

# 4. Verify models are ready
docker exec -it ollama ollama list
```

**Manual preloading after pull:**
```bash
# 1. Pull models
docker exec -it ollama ollama pull llama3.2:1b

# 2. Preload models
OLLAMA_PRELOAD_MODELS="llama3.2:1b" python3 scripts/preload_models.py

# 3. Models are now ready for instant use
```

---

## Performance Impact

### Without Preloading:
- First request: 5-30 seconds (model loading)
- Subsequent requests: < 1 second

### With Preloading:
- Preload time: 5-30 seconds (one-time during startup)
- All requests: < 1 second (instant)

**Benefits:**
- ✅ Eliminates cold-start latency
- ✅ Better user experience
- ✅ Predictable response times
- ✅ Models ready immediately after startup

**Trade-offs:**
- ⚠️ Uses memory/GPU during preload
- ⚠️ Slightly longer startup time
- ⚠️ One-time warmup cost per model

---

## Troubleshooting

### Models Not Preloading

**Check if models are pulled:**
```bash
docker exec -it ollama ollama list
```

**Check preloader logs:**
```bash
docker compose logs model_preloader
```

**Manually preload:**
```bash
docker exec -it ollama ollama run llama3.2:1b "Hi"
```

### Preloader Service Not Running

**Check service status:**
```bash
docker compose ps model_preloader
```

**Restart preloader:**
```bash
docker compose up -d model_preloader
```

**Note:** The preloader service exits after completion (restart: "no"). This is normal.

### Memory/GPU Issues

If you have limited resources:
- Preload only frequently-used models
- Use `OLLAMA_PRELOAD_MODELS` to specify subset
- Preload models one at a time

---

## Best Practices

1. **Preload Frequently Used Models**
   - Focus on models you use most often
   - Skip rarely-used models

2. **Monitor Resource Usage**
   - Check GPU memory: `nvidia-smi`
   - Check system memory: `free -h`

3. **Production Setup**
   - Always preload production models
   - Use docker-compose for automation
   - Monitor preload completion

4. **Development**
   - Preload can be skipped for faster iteration
   - Use manual preloading when needed

---

## Advanced: Custom Preload Script

You can create a custom preload script for specific needs:

```python
#!/usr/bin/env python3
import httpx
import time

OLLAMA_HOST = "http://localhost:11434"
MODELS = ["llama3.2:1b", "mistral"]

for model in MODELS:
    print(f"Preloading {model}...")
    start = time.time()
    
    httpx.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": model,
            "prompt": "Hi",
            "options": {"num_predict": 5}
        },
        timeout=120
    )
    
    elapsed = time.time() - start
    print(f"✓ {model} preloaded in {elapsed:.2f}s")
```

---

## Summary

Model preloading eliminates cold-start latency by loading models into memory/GPU before first use. Use the `model_preloader` service for automatic preloading, or run the scripts manually when needed.

**Quick Start:**
```bash
export OLLAMA_PRELOAD_MODELS="llama3.2:1b"
docker compose up -d
```

