# GPU Testing Guide

This guide explains how to verify that Ollama is actually using your GPU for inference.

## Quick Test

Run the GPU utilization test:

```bash
./scripts/test_gpu_utilization.sh
```

This will:
1. Check GPU access
2. Run a model inference
3. Monitor GPU usage in real-time
4. Report if GPU is being utilized

## Understanding GPU Utilization

### What to Look For

**GPU is Working:**
- GPU utilization increases during inference (typically 50-100%)
- GPU memory usage increases (varies by model size)
- Inference is faster than CPU-only
- Temperature may increase slightly

**GPU is NOT Working:**
- GPU utilization stays near 0% during inference
- No memory increase
- Inference is slow (CPU speed)
- CPU usage is high instead

### Expected Results

For a small model (like llama3.2:1b):
- **GPU Utilization:** Should jump to 50-100% during inference
- **Memory Increase:** 500 MB - 2 GB depending on model
- **Inference Time:** 5-15 seconds for a short response

For larger models (like llama3:8b):
- **GPU Utilization:** 80-100% during inference
- **Memory Increase:** 4-8 GB
- **Inference Time:** 10-30 seconds

## Manual Testing

### 1. Check GPU Access

```bash
# Check GPU in host
nvidia-smi

# Check GPU in container
docker exec ollama nvidia-smi
```

### 2. Monitor GPU During Inference

**Terminal 1 - Monitor GPU:**
```bash
# Monitor GPU continuously
watch -n 1 nvidia-smi
```

**Terminal 2:**
```bash
# Run inference
docker exec ollama ollama run llama3 "Write a story"
```

Watch Terminal 1 - you should see:
- GPU utilization spike to 50-100%
- Memory usage increase
- Temperature may rise slightly

### 3. Check Ollama GPU Detection

```bash
# Check if Ollama sees GPU (indirect check)
docker exec ollama ollama ps

# Check container GPU access
docker exec ollama nvidia-smi --query-gpu=name --format=csv
```

### 4. Compare CPU vs GPU Performance

**CPU-only test:**
```bash
# Temporarily disable GPU in docker-compose.yml
# Remove or comment out the deploy.resources section
docker compose restart ollama

# Time an inference
time docker exec ollama ollama run llama3 "Test"
```

**GPU-enabled test:**
```bash
# Re-enable GPU in docker-compose.yml
docker compose restart ollama

# Time the same inference
time docker exec ollama ollama run llama3 "Test"
```

GPU should be significantly faster (often 5-10x).

## Troubleshooting

### GPU Not Detected

**Symptoms:**
- `nvidia-smi` works on host but not in container
- Ollama runs but inference is slow

**Solutions:**
1. Verify NVIDIA Container Toolkit is installed:
   ```bash
   docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
   ```

2. Check Docker Compose GPU configuration:
   ```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: all
             capabilities: [gpu]
   ```

3. Restart Docker:
   ```bash
   sudo systemctl restart docker
   docker compose up -d ollama
   ```

### GPU Detected But Not Used

**Symptoms:**
- `nvidia-smi` works in container
- GPU utilization stays at 0% during inference
- Inference is slow

**Solutions:**
1. Check Ollama version (older versions may not support GPU):
   ```bash
   docker exec ollama ollama --version
   ```

2. Verify model supports GPU (most do, but check):
   ```bash
   docker exec ollama ollama show llama3
   ```

3. Check for GPU errors in logs:
   ```bash
   docker compose logs ollama | grep -i gpu
   docker compose logs ollama | grep -i cuda
   ```

### Low GPU Utilization

**Symptoms:**
- GPU utilization is 10-30% instead of 50-100%
- Inference is faster than CPU but not optimal

**Possible Causes:**
- Model is too small for GPU (uses CPU instead)
- Batch size is too small
- Model is quantized heavily (less GPU work)

**Solutions:**
- Try a larger model (7B+ parameters)
- Check model quantization level
- Monitor both GPU and CPU usage

## Advanced Monitoring

### Continuous GPU Monitoring

```bash
# Monitor GPU stats every second
while true; do
    clear
    nvidia-smi --query-gpu=utilization.gpu,memory.used,temperature.gpu --format=csv
    sleep 1
done
```

### GPU Memory Profiling

```bash
# Check GPU memory before/after
nvidia-smi --query-gpu=memory.used --format=csv,noheader

# Run inference
docker exec ollama ollama run llama3 "Test"

# Check again
nvidia-smi --query-gpu=memory.used --format=csv,noheader
```

### Performance Comparison

Create a benchmark script:

```bash
#!/bin/bash
MODEL="llama3"
PROMPT="Write a 200-word story about space exploration."

echo "Testing CPU performance..."
# Disable GPU temporarily
time docker exec ollama ollama run "$MODEL" "$PROMPT"

echo "Testing GPU performance..."
# Enable GPU
time docker exec ollama ollama run "$MODEL" "$PROMPT"
```

## Integration with CI/CD

The GPU utilization test can be integrated into CI/CD pipelines:

```yaml
# .github/workflows/gpu-test.yml
- name: Test GPU Utilization
  run: |
    ./scripts/test_gpu_utilization.sh
```

Note: CI environments typically don't have GPUs, so this test would be skipped or run conditionally.

## Summary

**Quick Test:**
```bash
./scripts/test_gpu_utilization.sh
```

**Manual Verification:**
1. `nvidia-smi` works in container
2. GPU utilization increases during inference
3. Memory usage increases
4. Inference is faster than CPU

**If GPU is not working:**
1. Check NVIDIA Container Toolkit
2. Verify Docker Compose GPU config
3. Restart Docker service
4. Check Ollama logs for errors

