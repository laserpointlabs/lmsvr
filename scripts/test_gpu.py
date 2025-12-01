#!/usr/bin/env python3
"""
GPU Access Test Script for Ollama (Python version)
Verifies that GPU is accessible to the Ollama container
"""
import subprocess
import sys
import os
from pathlib import Path

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def print_colored(text, color=Colors.NC):
    """Print colored text."""
    print(f"{color}{text}{Colors.NC}")

def run_command(cmd, check=True, capture_output=True):
    """Run a shell command."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result.stdout.strip() if capture_output else None
    except subprocess.CalledProcessError as e:
        if check:
            print_colored(f"Error: {e.stderr}", Colors.RED)
            sys.exit(1)
        return None

def check_nvidia_drivers():
    """Check if NVIDIA drivers are installed."""
    print_colored("Step 1: Checking NVIDIA drivers...", Colors.YELLOW)
    result = run_command("nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader", check=False)
    if result:
        print_colored("✓ NVIDIA drivers detected", Colors.GREEN)
        print(result.split('\n')[0])
        print()
        return True
    else:
        print_colored("✗ nvidia-smi not found", Colors.RED)
        print("  NVIDIA drivers may not be installed")
        return False

def check_nvidia_container_toolkit():
    """Check if NVIDIA Container Toolkit is installed."""
    print_colored("Step 2: Checking NVIDIA Container Toolkit...", Colors.YELLOW)
    result1 = run_command("which nvidia-container-runtime", check=False)
    result2 = run_command("docker info 2>/dev/null | grep -q nvidia", check=False)
    
    if result1 or result2:
        print_colored("✓ NVIDIA Container Toolkit detected", Colors.GREEN)
        print()
        return True
    else:
        print_colored("⚠ NVIDIA Container Toolkit not detected", Colors.YELLOW)
        print("  Install with: sudo apt-get install -y nvidia-container-toolkit")
        print("  Then restart Docker: sudo systemctl restart docker")
        print()
        return False

def check_docker_gpu_support():
    """Check if Docker can access GPU."""
    print_colored("Step 3: Checking Docker GPU support...", Colors.YELLOW)
    result = run_command(
        "docker run --rm --gpus all nvidia/cuda:11.0.3-base-ubuntu20.04 nvidia-smi 2>&1",
        check=False
    )
    if result and "NVIDIA-SMI" in result:
        print_colored("✓ Docker can access GPU", Colors.GREEN)
        print()
        return True
    else:
        print_colored("✗ Docker cannot access GPU", Colors.RED)
        print("  Check Docker daemon configuration")
        print("  Ensure /etc/docker/daemon.json includes nvidia runtime")
        return False

def check_ollama_container():
    """Check if Ollama container is running."""
    print_colored("Step 4: Checking Ollama container status...", Colors.YELLOW)
    result = run_command("docker ps | grep ollama", check=False)
    if result:
        print_colored("✓ Ollama container is running", Colors.GREEN)
        print()
        return True
    else:
        print_colored("⚠ Ollama container is not running", Colors.YELLOW)
        print("  Starting Ollama container...")
        run_command("docker compose up -d ollama", check=False)
        import time
        time.sleep(5)
        return True

def test_gpu_in_container():
    """Test GPU access inside Ollama container."""
    print_colored("Step 5: Testing GPU access inside Ollama container...", Colors.YELLOW)
    result = run_command("docker exec ollama nvidia-smi 2>&1", check=False)
    if result and "NVIDIA-SMI" in result:
        print_colored("✓ GPU is accessible inside Ollama container", Colors.GREEN)
        print()
        print("GPU Information:")
        gpu_info = run_command(
            "docker exec ollama nvidia-smi --query-gpu=index,name,memory.total,memory.used --format=csv,noheader",
            check=False
        )
        if gpu_info:
            print(gpu_info)
        print()
        return True
    else:
        print_colored("✗ GPU is NOT accessible inside Ollama container", Colors.RED)
        print()
        print("Troubleshooting steps:")
        print("1. Ensure docker-compose.yml has GPU configuration")
        print("2. Restart Docker: sudo systemctl restart docker")
        print("3. Recreate containers: docker compose up -d --force-recreate ollama")
        return False

def test_ollama_gpu_detection():
    """Test if Ollama detects GPU."""
    print_colored("Step 6: Testing Ollama GPU detection...", Colors.YELLOW)
    result = run_command("docker exec ollama ollama ps 2>&1", check=False)
    if result and ("gpu" in result.lower() or "cuda" in result.lower() or "nvidia" in result.lower()):
        print_colored("✓ Ollama detects GPU", Colors.GREEN)
        print()
        return True
    elif run_command("docker exec ollama ollama list 2>&1", check=False):
        print_colored("⚠ Ollama is running but GPU detection unclear", Colors.YELLOW)
        print("  This may be normal if no models are loaded")
        print()
        return True
    else:
        print_colored("✗ Cannot communicate with Ollama", Colors.RED)
        print("  Check container logs: docker logs ollama")
        return False

def main():
    """Main test function."""
    print_colored("=" * 40, Colors.BLUE)
    print_colored("GPU Access Test for Ollama", Colors.BLUE)
    print_colored("=" * 40, Colors.BLUE)
    print()
    
    all_passed = True
    
    # Run all checks
    all_passed &= check_nvidia_drivers()
    if not all_passed:
        sys.exit(1)
    
    check_nvidia_container_toolkit()  # Warning only
    
    all_passed &= check_docker_gpu_support()
    if not all_passed:
        sys.exit(1)
    
    check_ollama_container()
    
    all_passed &= test_gpu_in_container()
    if not all_passed:
        sys.exit(1)
    
    test_ollama_gpu_detection()  # Info only
    
    # Summary
    print_colored("=" * 40, Colors.BLUE)
    print_colored("GPU Access Test Complete!", Colors.GREEN)
    print_colored("=" * 40, Colors.BLUE)
    print()
    print("GPU is configured and accessible to Ollama.")
    print("You can now pull and run models with GPU acceleration.")
    print()
    print("Example:")
    print("  docker exec -it ollama ollama pull llama3")
    print("  docker exec -it ollama ollama run llama3")

if __name__ == "__main__":
    main()

