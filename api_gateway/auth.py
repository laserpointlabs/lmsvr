"""
Authentication middleware for API key validation.
"""
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
try:
    from .database import get_db_session, APIKey, Customer
except ImportError:
    from database import get_db_session, APIKey, Customer
import hashlib
from datetime import datetime

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)


def hash_api_key(key: str) -> str:
    """Hash an API key using SHA-256."""
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(api_key: str, db: Session) -> tuple[Customer, APIKey]:
    """
    Verify API key and return customer and API key objects.
    
    Raises HTTPException if key is invalid.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not api_key:
        logger.warning("API key value is missing.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # Handle "Bearer <key>" format
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]
    
    # Hash the provided key
    key_hash = hash_api_key(api_key)
    logger.debug(f"Attempting to verify key with hash: {key_hash[:20]}...")
    
    # Look up the key in database
    db_key = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.active == True
    ).first()
    
    if not db_key:
        logger.warning(f"Invalid API key hash: {key_hash[:20]}...")
        # Debug: Check total keys in DB
        total_keys = db.query(APIKey).count()
        logger.debug(f"Total API keys in database: {total_keys}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Check expiration
    if db_key.expires_at and db_key.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired"
        )
    
    # Get customer
    customer = db.query(Customer).filter(Customer.id == db_key.customer_id).first()
    
    if not customer or not customer.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer account is inactive"
        )
    
    return customer, db_key


async def get_current_customer(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db_session)
) -> tuple[Customer, APIKey]:
    """
    Dependency function for FastAPI to get current customer from API key.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated: Missing or invalid API key format (Bearer token required)"
        )
    
    return verify_api_key(credentials.credentials, db)

