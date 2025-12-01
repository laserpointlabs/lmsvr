"""
Integration tests for Ollama connectivity and model operations.
"""
import pytest
import httpx
import os
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def api_base_url():
    """Get API base URL from environment or use default."""
    return os.getenv("API_BASE_URL", "http://localhost:8001")


@pytest.fixture
def ollama_available():
    """Check if Ollama is available."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


@pytest.mark.asyncio
@pytest.mark.integration
async def test_ollama_service_available(api_base_url):
    """Test that Ollama service is accessible."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{api_base_url}/health/ollama")
            # Should return 200 if Ollama is available, 503 if not
            assert response.status_code in [200, 503]
        except httpx.ConnectError:
            pytest.skip("API Gateway not running")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_ollama_api_tags_endpoint():
    """Test direct Ollama API access."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                data = response.json()
                assert "models" in data
        except httpx.ConnectError:
            pytest.skip("Ollama service not running")


@pytest.mark.integration
def test_ollama_cli_available(ollama_available):
    """Test that Ollama CLI is available."""
    if not ollama_available:
        pytest.skip("Ollama CLI not available")
    
    result = subprocess.run(
        ["ollama", "--version"],
        capture_output=True,
        text=True,
        timeout=5
    )
    assert result.returncode == 0
    assert "ollama" in result.stdout.lower() or "version" in result.stdout.lower()


@pytest.mark.integration
def test_ollama_list_models(ollama_available):
    """Test listing models via Ollama CLI."""
    if not ollama_available:
        pytest.skip("Ollama CLI not available")
    
    result = subprocess.run(
        ["ollama", "list"],
        capture_output=True,
        text=True,
        timeout=10
    )
    assert result.returncode == 0
    # Should return list (may be empty)

