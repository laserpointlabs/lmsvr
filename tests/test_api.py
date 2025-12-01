"""
API Gateway integration tests.
"""
import pytest
import httpx
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_gateway.database import get_db_session_sync, Customer, APIKey
from api_gateway.auth import hash_api_key


@pytest.fixture
def api_base_url():
    """Get API base URL from environment or use default."""
    return os.getenv("API_BASE_URL", "http://localhost:8001")


@pytest.fixture
def test_customer():
    """Create a test customer and return customer ID."""
    import secrets
    db = get_db_session_sync()
    try:
        # Use unique email for each test run
        email = f"test_{secrets.token_hex(4)}@example.com"
        
        customer = Customer(
            name="Test Customer",
            email=email,
            monthly_budget=100.0,
            active=True
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        yield customer.id
        # Cleanup
        db.delete(customer)
        db.commit()
    finally:
        db.close()


@pytest.fixture
def test_api_key(test_customer):
    """Create a test API key and return it."""
    db = get_db_session_sync()
    try:
        import secrets
        api_key = f"sk_{secrets.token_urlsafe(32)}"
        key_hash = hash_api_key(api_key)
        
        db_key = APIKey(
            customer_id=test_customer,
            key_hash=key_hash,
            active=True
        )
        db.add(db_key)
        db.commit()
        yield api_key
        # Cleanup
        db.delete(db_key)
        db.commit()
    finally:
        db.close()


@pytest.mark.asyncio
async def test_health_endpoint(api_base_url):
    """Test health check endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{api_base_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "api_gateway"


@pytest.mark.asyncio
async def test_ollama_health_endpoint(api_base_url):
    """Test Ollama health check endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{api_base_url}/health/ollama")
        # May return 503 if Ollama is not available, which is acceptable
        assert response.status_code in [200, 503]


@pytest.mark.asyncio
async def test_models_endpoint_requires_auth(api_base_url):
    """Test that models endpoint requires authentication."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{api_base_url}/api/models")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_models_endpoint_with_auth(api_base_url, test_api_key):
    """Test models endpoint with valid API key."""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {test_api_key}"}
        response = await client.get(f"{api_base_url}/api/models", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "models" in data


@pytest.mark.asyncio
async def test_openai_models_endpoint(api_base_url, test_api_key):
    """Test OpenAI-compatible models endpoint."""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {test_api_key}"}
        response = await client.get(f"{api_base_url}/v1/models", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "list"
        assert "data" in data


@pytest.mark.asyncio
async def test_invalid_api_key(api_base_url):
    """Test that invalid API key is rejected."""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": "Bearer invalid_key_12345"}
        response = await client.get(f"{api_base_url}/api/models", headers=headers)
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_endpoint_requires_auth(api_base_url):
    """Test that chat endpoint requires authentication."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{api_base_url}/api/chat",
            json={"model": "test", "messages": []}
        )
        assert response.status_code == 401

