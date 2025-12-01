"""
Database tests.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from api_gateway.database import (
    get_db_session_sync,
    Customer,
    APIKey,
    UsageLog,
    PricingConfig,
    ModelMetadata,
    init_db
)
from api_gateway.auth import hash_api_key


@pytest.fixture(scope="function")
def db_session():
    """Get database session for testing."""
    db = get_db_session_sync()
    try:
        # Initialize database
        init_db()
        yield db
        # Cleanup - rollback any uncommitted changes
        db.rollback()
    finally:
        db.close()


def test_create_customer(db_session):
    """Test creating a customer."""
    import secrets
    email = f"test_{secrets.token_hex(4)}@example.com"
    customer = Customer(
        name="Test Customer",
        email=email,
        monthly_budget=100.0
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    
    assert customer.id is not None
    assert customer.name == "Test Customer"
    assert customer.email == email
    assert customer.monthly_budget == 100.0
    
    # Cleanup
    db_session.delete(customer)
    db_session.commit()


def test_create_api_key(db_session):
    """Test creating an API key."""
    import secrets
    email = f"test_{secrets.token_hex(4)}@example.com"
    customer = Customer(
        name="Test Customer",
        email=email
    )
    db_session.add(customer)
    db_session.commit()
    
    api_key = "sk_test_key_12345"
    key_hash = hash_api_key(api_key)
    
    db_key = APIKey(
        customer_id=customer.id,
        key_hash=key_hash,
        active=True
    )
    db_session.add(db_key)
    db_session.commit()
    db_session.refresh(db_key)
    
    assert db_key.id is not None
    assert db_key.customer_id == customer.id
    assert db_key.key_hash == key_hash


def test_create_pricing_config(db_session):
    """Test creating pricing configuration."""
    import secrets
    model_name = f"test-model-{secrets.token_hex(4)}"
    pricing = PricingConfig(
        model_name=model_name,
        per_request_cost=0.001,
        per_model_cost=0.002
    )
    db_session.add(pricing)
    db_session.commit()
    db_session.refresh(pricing)
    
    assert pricing.id is not None
    assert pricing.model_name == model_name
    assert pricing.per_request_cost == 0.001
    assert pricing.per_model_cost == 0.002
    
    # Cleanup
    db_session.delete(pricing)
    db_session.commit()


def test_create_usage_log(db_session):
    """Test creating usage log."""
    import secrets
    email = f"test_{secrets.token_hex(4)}@example.com"
    customer = Customer(
        name="Test Customer",
        email=email
    )
    db_session.add(customer)
    db_session.commit()
    
    api_key = APIKey(
        customer_id=customer.id,
        key_hash=hash_api_key("test_key"),
        active=True
    )
    db_session.add(api_key)
    db_session.commit()
    
    usage_log = UsageLog(
        customer_id=customer.id,
        api_key_id=api_key.id,
        endpoint="/api/chat",
        model="test-model",
        cost=0.01
    )
    db_session.add(usage_log)
    db_session.commit()
    db_session.refresh(usage_log)
    
    assert usage_log.id is not None
    assert usage_log.customer_id == customer.id
    assert usage_log.endpoint == "/api/chat"
    assert usage_log.cost == 0.01

