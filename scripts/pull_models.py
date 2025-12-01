#!/usr/bin/env python3

"""
Script to pull Ollama models specified in environment variable.
Usage: OLLAMA_MODELS="llama3.2:1b mistral" python3 scripts/pull_models.py
"""

import os
import sys
import time
import httpx
from typing import List

# Colors for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODELS_STR = os.getenv("OLLAMA_MODELS", "")

def wait_for_ollama(max_retries: int = 30, retry_delay: int = 2) -> bool:
    """Wait for Ollama to be ready."""
    print(f"{YELLOW}Waiting for Ollama to be ready...{NC}")
    
    for i in range(max_retries):
        try:
            response = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
            if response.status_code == 200:
                print(f"{GREEN}✓ Ollama is ready{NC}")
                return True
        except Exception:
            pass
        
        print(f"Waiting... ({i+1}/{max_retries})")
        time.sleep(retry_delay)
    
    print(f"{RED}✗ Ollama did not become ready in time{NC}")
    return False

def get_existing_models() -> List[str]:
    """Get list of existing models."""
    try:
        response = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return [model.get("name", "") for model in data.get("models", [])]
    except Exception as e:
        print(f"{RED}Error getting existing models: {e}{NC}")
    return []

def pull_model(model: str) -> bool:
    """Pull a model from Ollama."""
    try:
        print(f"{YELLOW}Pulling model: {model}{NC}")
        
        # Start pull (this is async, so we just trigger it)
        response = httpx.post(
            f"{OLLAMA_HOST}/api/pull",
            json={"name": model},
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"{GREEN}  ✓ Started pulling {model}{NC}")
            
            # Poll for completion
            print(f"{YELLOW}  Waiting for {model} to finish downloading...{NC}")
            max_wait = 300  # 5 minutes max per model
            waited = 0
            
            while waited < max_wait:
                existing = get_existing_models()
                if model in existing:
                    print(f"{GREEN}  ✓ Model {model} downloaded successfully{NC}")
                    return True
                time.sleep(5)
                waited += 5
                if waited % 30 == 0:
                    print(f"  Still downloading... ({waited}s)")
            
            print(f"{YELLOW}  ⚠ Pull may still be in progress (timeout reached){NC}")
            return True
        else:
            print(f"{RED}  ✗ Failed to pull {model}: {response.status_code}{NC}")
            return False
    except Exception as e:
        print(f"{RED}  ✗ Error pulling {model}: {e}{NC}")
        return False

def main():
    """Main function."""
    print(f"{BLUE}========================================{NC}")
    print(f"{BLUE}Ollama Model Puller{NC}")
    print(f"{BLUE}========================================{NC}")
    print("")
    print(f"Ollama Host: {OLLAMA_HOST}")
    
    if not MODELS_STR:
        print(f"{YELLOW}No models specified in OLLAMA_MODELS environment variable{NC}")
        print("Set OLLAMA_MODELS to pull models automatically, e.g.:")
        print("  OLLAMA_MODELS=\"llama3.2:1b mistral codellama\"")
        return 0
    
    models = [m.strip() for m in MODELS_STR.split() if m.strip()]
    print(f"Models to pull: {', '.join(models)}")
    print("")
    
    # Wait for Ollama
    if not wait_for_ollama():
        return 1
    
    print("")
    
    # Get existing models
    existing_models = get_existing_models()
    
    # Pull each model
    success_count = 0
    for model in models:
        if model in existing_models:
            print(f"{GREEN}✓ Model {model} already exists, skipping{NC}")
            success_count += 1
        else:
            if pull_model(model):
                success_count += 1
        print("")
    
    print(f"{GREEN}========================================{NC}")
    print(f"{GREEN}Model pull process completed{NC}")
    print(f"{GREEN}  Successfully processed: {success_count}/{len(models)}{NC}")
    print(f"{GREEN}========================================{NC}")
    
    # List available models
    print("")
    print(f"{BLUE}Available models:{NC}")
    try:
        response = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        if response.status_code == 200:
            data = response.json()
            for model in data.get("models", []):
                name = model.get("name", "unknown")
                size = model.get("size", 0)
                size_gb = size / (1024**3)
                print(f"  - {name} ({size_gb:.2f} GB)")
    except Exception as e:
        print(f"{RED}Could not list models: {e}{NC}")
    
    return 0 if success_count == len(models) else 1

if __name__ == "__main__":
    sys.exit(main())




