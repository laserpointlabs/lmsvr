#!/usr/bin/env python3

"""
Test GPU Utilization for Ollama
Verifies that Ollama is actually using the GPU during inference
"""

import subprocess
import time
import sys
import json
from typing import Dict, List, Tuple

# Colors
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'


def run_command(cmd: List[str], check: bool = True) -> Tuple[str, int]:
    """Run a shell command and return output and exit code."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check
        )
        return result.stdout.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout.strip() + e.stderr.strip(), e.returncode


def get_gpu_stats() -> Dict[str, int]:
    """Get current GPU statistics."""
    cmd = [
        'nvidia-smi',
        '--query-gpu=utilization.gpu,memory.used,temperature.gpu',
        '--format=csv,noheader,nounits'
    ]
    output, code = run_command(cmd, check=False)
    if code != 0:
        return None
    
    parts = output.split(', ')
    return {
        'utilization': int(parts[0]),
        'memory_mb': int(parts[1]),
        'temperature': int(parts[2])
    }


def check_ollama_running() -> bool:
    """Check if Ollama container is running."""
    output, code = run_command(['docker', 'ps', '--filter', 'name=ollama', '--format', '{{.Names}}'])
    return 'ollama' in output


def get_available_model() -> str:
    """Get an available Ollama model or pull a test model."""
    output, code = run_command(['docker', 'exec', 'ollama', 'ollama', 'list'])
    
    if code == 0 and output:
        lines = output.strip().split('\n')
        if len(lines) > 1:  # Skip header
            # Get first model name
            model = lines[1].split()[0]
            return model
    
    # No models, pull a small one
    print(f"{YELLOW}⚠ No models found. Pulling llama3.2:1b...{NC}")
    print("  This may take a few minutes...")
    run_command(['docker', 'exec', 'ollama', 'ollama', 'pull', 'llama3.2:1b'])
    return 'llama3.2:1b'


def monitor_gpu_during_inference(model: str, duration: int = 30) -> Tuple[List[Dict], float]:
    """Monitor GPU during inference and return stats."""
    stats = []
    
    # Start monitoring
    print(f"{YELLOW}Starting inference test (monitoring for {duration} seconds)...{NC}")
    print(f"{YELLOW}Monitoring GPU utilization...{NC}\n")
    
    # Start inference in background
    inference_cmd = [
        'docker', 'exec', 'ollama', 'ollama', 'run', model,
        'Write a short story about a robot learning to paint. Make it exactly 100 words.'
    ]
    
    start_time = time.time()
    process = subprocess.Popen(
        inference_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Monitor GPU
    for i in range(duration):
        try:
            gpu_stats = get_gpu_stats()
            gpu_stats['timestamp'] = time.time() - start_time
            stats.append(gpu_stats)
            print(f"[{i+1}/{duration}] GPU: {gpu_stats['utilization']}% | "
                  f"Memory: {gpu_stats['memory_mb']} MB | "
                  f"Temp: {gpu_stats['temperature']}°C")
        except Exception as e:
            print(f"{YELLOW}⚠ Could not read GPU stats: {e}{NC}")
        
        time.sleep(1)
    
    # Wait for inference to complete
    process.wait()
    inference_time = time.time() - start_time
    
    return stats, inference_time


def main():
    print(f"{BLUE}{'='*40}{NC}")
    print(f"{BLUE}GPU Utilization Test for Ollama{NC}")
    print(f"{BLUE}{'='*40}{NC}\n")
    
    # Check prerequisites
    print(f"{YELLOW}Checking prerequisites...{NC}")
    
    # Check nvidia-smi
    _, code = run_command(['nvidia-smi', '--version'], check=False)
    if code != 0:
        print(f"{RED}✗ nvidia-smi not found{NC}")
        print("  NVIDIA drivers may not be installed")
        sys.exit(1)
    print(f"{GREEN}✓ nvidia-smi available{NC}")
    
    # Check Ollama container
    if not check_ollama_running():
        print(f"{RED}✗ Ollama container is not running{NC}")
        print("  Start it with: docker compose up -d ollama")
        sys.exit(1)
    print(f"{GREEN}✓ Ollama container is running{NC}")
    
    # Check GPU in container
    print(f"\n{YELLOW}Checking GPU access in container...{NC}")
    _, code = run_command(['docker', 'exec', 'ollama', 'nvidia-smi'], check=False)
    if code != 0:
        print(f"{RED}✗ GPU not accessible in container{NC}")
        print("  Check Docker GPU configuration")
        sys.exit(1)
    print(f"{GREEN}✓ GPU accessible in container{NC}")
    
    # Get GPU info
    output, _ = run_command([
        'nvidia-smi',
        '--query-gpu=name,driver_version,memory.total',
        '--format=csv,noheader'
    ])
    print(f"  {output}")
    
    # Get model
    print(f"\n{YELLOW}Checking for available models...{NC}")
    model = get_available_model()
    print(f"{GREEN}✓ Using model: {model}{NC}")
    
    # Baseline stats
    print(f"\n{YELLOW}Baseline GPU usage (before inference):{NC}")
    baseline = get_gpu_stats()
    print(f"  GPU Utilization: {baseline['utilization']}%")
    print(f"  Memory Used: {baseline['memory_mb']} MB")
    
    # Monitor during inference
    print()
    stats, inference_time = monitor_gpu_during_inference(model)
    
    # Final stats
    print(f"\n{YELLOW}Final GPU usage (after inference):{NC}")
    final = get_gpu_stats()
    print(f"  GPU Utilization: {final['utilization']}%")
    print(f"  Memory Used: {final['memory_mb']} MB")
    
    # Calculate increases
    util_increase = final['utilization'] - baseline['utilization']
    mem_increase = final['memory_mb'] - baseline['memory_mb']
    
    # Find peak usage
    peak_util = max(s['utilization'] for s in stats)
    peak_mem = max(s['memory_mb'] for s in stats)
    
    # Results
    print(f"\n{BLUE}{'='*40}{NC}")
    print(f"{BLUE}Results{NC}")
    print(f"{BLUE}{'='*40}{NC}")
    print(f"  Inference Time: {inference_time:.1f} seconds")
    print(f"  Peak GPU Utilization: {peak_util}%")
    print(f"  Peak Memory Usage: {peak_mem} MB")
    print(f"  GPU Utilization Increase: {util_increase}%")
    print(f"  Memory Increase: {mem_increase} MB")
    print()
    
    # Determine if GPU was used
    if util_increase > 10 or mem_increase > 50:
        print(f"{GREEN}✓ GPU IS BEING UTILIZED{NC}")
        print("  GPU usage increased significantly during inference")
        print("  This indicates Ollama is using the GPU")
        sys.exit(0)
    elif util_increase > 0 or mem_increase > 0:
        print(f"{YELLOW}⚠ GPU usage detected but may be minimal{NC}")
        print(f"  GPU utilization: {util_increase}% increase")
        print(f"  Memory increase: {mem_increase} MB")
        print("  This may indicate GPU is being used, but check model size")
        sys.exit(0)
    else:
        print(f"{RED}✗ GPU DOES NOT APPEAR TO BE UTILIZED{NC}")
        print("  No significant GPU usage detected during inference")
        print("  Ollama may be using CPU instead")
        print()
        print("Troubleshooting:")
        print("  1. Check Docker GPU configuration:")
        print("     docker exec ollama nvidia-smi")
        print("  2. Verify NVIDIA Container Toolkit is installed")
        print("  3. Check docker-compose.yml GPU settings")
        print("  4. Restart Docker: sudo systemctl restart docker")
        sys.exit(1)


if __name__ == '__main__':
    main()

