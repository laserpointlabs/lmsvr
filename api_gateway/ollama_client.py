"""
Client wrapper for Ollama API calls.
"""
import httpx
import os
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


async def list_models() -> list[Dict[str, Any]]:
    """List all available models from Ollama."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
            else:
                logger.error(f"Failed to list models: {response.status_code}")
                return []
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return []


async def chat(model: str, messages: list, stream: bool = False, options: Optional[Dict] = None) -> Dict[str, Any]:
    """Send chat request to Ollama."""
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream
    }
    if options:
        payload["options"] = options
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload
        )
        response.raise_for_status()
        return response.json()


async def generate(model: str, prompt: str, stream: bool = False, options: Optional[Dict] = None) -> Dict[str, Any]:
    """Send generate request to Ollama."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream
    }
    if options:
        payload["options"] = options
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload
        )
        response.raise_for_status()
        return response.json()


async def check_ollama_health() -> bool:
    """Check if Ollama is accessible."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return response.status_code == 200
    except Exception:
        return False

