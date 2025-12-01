#!/usr/bin/env python3
"""
Preload/warmup Ollama models to avoid first-request latency.
This script loads models into memory/GPU so they're ready for immediate use.
"""
import os
import sys
import httpx
import time
from typing import List

# Colors for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODELS_STR = os.getenv("OLLAMA_PRELOAD_MODELS", os.getenv("OLLAMA_MODELS", ""))


def wait_for_ollama(max_retries: int = 30) -> bool:
    """Wait for Ollama to be ready."""
    print(f"{YELLOW}Waiting for Ollama to be ready...{NC}")
    for i in range(max_retries):
        try:
            response = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
            if response.status_code == 200:
                print(f"{GREEN}✓ Ollama is ready{NC}")
                return True
        except Exception:
            pass
        print(f"  Waiting... ({i+1}/{max_retries})")
        time.sleep(2)
    print(f"{RED}✗ Ollama did not become ready in time{NC}")
    return False


def get_available_models() -> List[str]:
    """Get list of available models from Ollama."""
    try:
        response = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return [model.get("name", "") for model in data.get("models", [])]
    except Exception as e:
        print(f"{RED}Error getting models: {e}{NC}")
    return []


def preload_model(model: str) -> bool:
    """Preload a model by making a warmup request."""
    try:
        print(f"{YELLOW}Preloading model: {model}{NC}")
        
        # Make a small warmup request to load the model into memory/GPU
        # This is a minimal request that will trigger model loading
        warmup_prompt = "Hi"
        
        start_time = time.time()
        
        response = httpx.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model,
                "prompt": warmup_prompt,
                "stream": False,
                "options": {
                    "num_predict": 5,  # Very short response to minimize cost/time
                    "temperature": 0.1
                }
            },
            timeout=120  # Allow up to 2 minutes for model loading
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            print(f"{GREEN}  ✓ Model {model} preloaded successfully ({elapsed:.2f}s){NC}")
            return True
        else:
            print(f"{RED}  ✗ Failed to preload {model}: {response.status_code}{NC}")
            try:
                error_data = response.json()
                print(f"  Error: {error_data}")
            except:
                print(f"  Error: {response.text}")
            return False
            
    except httpx.TimeoutException:
        print(f"{YELLOW}  ⚠ Timeout preloading {model} (may still be loading){NC}")
        return False
    except Exception as e:
        print(f"{RED}  ✗ Error preloading {model}: {e}{NC}")
        return False


def main():
    """Main function."""
    print(f"{BLUE}========================================{NC}")
    print(f"{BLUE}Ollama Model Preloader{NC}")
    print(f"{BLUE}========================================{NC}")
    print("")
    print(f"Ollama Host: {OLLAMA_HOST}")
    
    if not MODELS_STR:
        print(f"{YELLOW}No models specified for preloading{NC}")
        print("Set OLLAMA_PRELOAD_MODELS or OLLAMA_MODELS environment variable, e.g.:")
        print("  OLLAMA_PRELOAD_MODELS=\"llama3.2:1b mistral codellama\"")
        return 0
    
    models = [m.strip() for m in MODELS_STR.split() if m.strip()]
    print(f"Models to preload: {', '.join(models)}")
    print("")
    
    # Wait for Ollama
    if not wait_for_ollama():
        return 1
    
    print("")
    
    # Get available models
    available_models = get_available_models()
    if not available_models:
        print(f"{RED}No models found in Ollama{NC}")
        print("Make sure models are pulled first using OLLAMA_MODELS")
        return 1
    
    print(f"{BLUE}Available models: {', '.join(available_models)}{NC}")
    print("")
    
    # Preload each specified model
    success_count = 0
    for model in models:
        if model not in available_models:
            print(f"{YELLOW}⚠ Model {model} not found, skipping preload{NC}")
            print(f"  Make sure to pull it first: docker exec -it ollama ollama pull {model}")
            continue
        
        if preload_model(model):
            success_count += 1
        print("")
    
    print(f"{GREEN}========================================{NC}")
    print(f"{GREEN}Model preload process completed{NC}")
    print(f"{GREEN}  Successfully preloaded: {success_count}/{len(models)}{NC}")
    print(f"{GREEN}========================================{NC}")
    
    # Return 0 if at least one model was preloaded, or if no models were specified
    # Only return 1 if models were specified but none could be preloaded
    if len(models) == 0:
        return 0
    return 0 if success_count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())

