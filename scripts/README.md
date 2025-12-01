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

## Other Scripts

Additional utility scripts can be added here for:
- Database backups
- Log analysis
- Performance testing
- Deployment automation

## Documentation

For detailed GPU testing guide, see: `docs/GPU_TESTING.md`
