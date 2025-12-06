import logging
import json
from datetime import datetime
from sqlalchemy.orm import Session
from api_gateway.database import ExternalAPIUsage, SessionLocal

logger = logging.getLogger(__name__)

def track_external_api_call(
    service_name: str,
    endpoint: str,
    method: str = "GET",
    status_code: int = 200,
    cost_credits: int = 0,
    metadata: dict = None
):
    """
    Track an external API call in the database.
    This function handles its own database session to be used from anywhere.
    """
    try:
        db: Session = SessionLocal()
        try:
            usage = ExternalAPIUsage(
                service_name=service_name,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                cost_credits=cost_credits,
                metadata_json=json.dumps(metadata) if metadata else None,
                timestamp=datetime.utcnow()
            )
            db.add(usage)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to save API usage log: {e}")
            db.rollback()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to create DB session for tracking: {e}")
