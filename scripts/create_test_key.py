import sys
import os
import secrets
from datetime import datetime

# Add parent dir to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "api_gateway"))

from api_gateway.database import get_db_session, Customer, APIKey
from api_gateway.auth import hash_api_key

def create_test_key():
    db = next(get_db_session())

    # Create or get test customer
    customer = db.query(Customer).filter(Customer.email == "test@example.com").first()
    if not customer:
        customer = Customer(name="Test User", email="test@example.com")
        db.add(customer)
        db.commit()
        print(f"Created customer: {customer.id}")

    # Create API key
    raw_key = f"sk_{secrets.token_urlsafe(16)}"
    key_hash = hash_api_key(raw_key)

    api_key = APIKey(
        customer_id=customer.id,
        key_hash=key_hash,
        active=True
    )
    db.add(api_key)
    db.commit()

    print(f"Created API Key: {raw_key}")
    return raw_key

if __name__ == "__main__":
    create_test_key()
