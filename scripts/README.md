# Scripts Directory

This directory contains utility scripts for the Ollama API Gateway project.

## GPU Testing Scripts

### Basic GPU Access Test

**`test_gpu.sh`** / **`test_gpu.py`**
- Verifies NVIDIA drivers are installed
- Checks NVIDIA Container Toolkit
- Tests Docker GPU access
- Verifies Ollama can see GPU

**Usage:**
```bash
./scripts/test_gpu.sh
# or
python3 scripts/test_gpu.py
```

### GPU Utilization Test (Recommended)

**`test_gpu_utilization.sh`** / **`test_gpu_utilization.py`**
- Actually runs inference and monitors GPU usage
- Verifies GPU is being utilized during model inference
- Shows real-time GPU stats (utilization, memory, temperature)
- Provides clear pass/fail results

**Usage:**
```bash
./scripts/test_gpu_utilization.sh
# or
python3 scripts/test_gpu_utilization.py
```

**What it does:**
1. Checks prerequisites (nvidia-smi, Ollama container)
2. Verifies GPU access in container
3. Gets baseline GPU stats
4. Runs a model inference
5. Monitors GPU during inference (30 seconds)
6. Compares baseline vs. peak usage
7. Determines if GPU was actually used

**Expected Output:**
- If GPU is working: Shows increased GPU utilization and memory usage during inference
- If GPU is not working: Shows no significant increase, indicates CPU usage

**Troubleshooting:**
- If GPU utilization doesn't increase, check Docker GPU configuration
- Verify NVIDIA Container Toolkit is installed
- Check docker-compose.yml GPU settings
- Restart Docker service

## Model Preloading

### Automatic Model Loading

**`ollama-start.sh`** (Active Script)
- Entrypoint script that starts Ollama and preloads models
- Automatically loads specified models when Ollama container starts
- Pulls models if they're not already available
- Keeps models loaded permanently (with `OLLAMA_KEEP_ALIVE=-1`)
- Configured via `OLLAMA_PRELOAD_MODELS` environment variable

**Configuration:**
Set `OLLAMA_PRELOAD_MODELS` in your `.env` file with a comma-separated list:
```bash
OLLAMA_PRELOAD_MODELS="qwen3-coder:30b,devstral,qwen2.5-coder:1.5b-base,nomic-embed-text"
```

**How it works:**
1. Script starts Ollama server in the background
2. Waits for Ollama service to be ready (checks `ollama list`)
3. Reads `OLLAMA_PRELOAD_MODELS` environment variable
4. For each model in the comma-separated list:
   - Trims whitespace from model name
   - Checks if model exists locally (`ollama list`)
   - Pulls model if not found (`ollama pull`)
   - Loads model into GPU memory (`ollama run` for regular models)
   - Model stays loaded forever due to `OLLAMA_KEEP_ALIVE=-1`
5. Shows summary of loaded models (`ollama ps`)
6. Keeps container running

**Model Types:**
- **Regular Models** (chat, code generation): 
  - Loaded via `ollama run` command
  - Appear in `ollama ps` with "Forever" status
  - Stay loaded in GPU memory permanently
  
- **Embedding Models**:
  - **Cannot be loaded via `ollama run`** (they don't support the generate API)
  - Automatically detected and loaded via `/api/embeddings` endpoint
  - Once loaded, appear in `ollama ps` with "Forever" status
  - Stay loaded in GPU memory permanently
  - **Note**: This is not a container rebuild issue - embedding models require a different API endpoint

**Environment Variables:**
- `OLLAMA_PRELOAD_MODELS`: Comma-separated list of models (e.g., `"model1,model2,model3"`)
- `OLLAMA_KEEP_ALIVE`: Set to `-1` for permanent loading (default: `-1`)
- `OLLAMA_MAX_LOADED_MODELS`: Max concurrent models (default: `6` for 4 GPUs)

**Usage:**
The script runs automatically as the container entrypoint. To verify it's working:
```bash
# Check loaded models
docker exec ollama ollama ps

# Check container logs
docker compose logs ollama | grep -E "(Preloading|loaded|complete)"
```

**Troubleshooting:**
- Models not loading: Check `OLLAMA_PRELOAD_MODELS` in `.env` file
- Models unloading: Verify `OLLAMA_KEEP_ALIVE=-1` is set
- Out of memory: Reduce number of models or increase `OLLAMA_MAX_LOADED_MODELS`
- Check logs: `docker compose logs ollama`

## Other Scripts

Additional utility scripts can be added here for:
- Database backups
- Log analysis
- Performance testing
- Deployment automation

## Documentation

For detailed GPU testing guide, see: `docs/GPU_TESTING.md`
