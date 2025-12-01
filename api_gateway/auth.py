"""
Authentication middleware for API key validation.
"""
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from database import get_db_session, APIKey, Customer
import hashlib
from datetime import datetime

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


def hash_api_key(key: str) -> str:
    """Hash an API key using SHA-256."""
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(api_key: str, db: Session) -> tuple[Customer, APIKey]:
    """
    Verify API key and return customer and API key objects.
    
    Raises HTTPException if key is invalid.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # Handle "Bearer <key>" format
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]
    
    # Hash the provided key
    key_hash = hash_api_key(api_key)
    
    # Look up the key in database
    db_key = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.active == True
    ).first()
    
    if not db_key:
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
    authorization: str = Security(api_key_header),
    db: Session = Depends(get_db_session)
) -> tuple[Customer, APIKey]:
    """
    Dependency function for FastAPI to get current customer from API key.
    """
    return verify_api_key(authorization, db)

