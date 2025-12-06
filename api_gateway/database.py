"""
Database setup and configuration for SQLite database.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)
    monthly_budget = Column(Float, nullable=True)

    api_keys = relationship("APIKey", back_populates="customer", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="customer")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    key_hash = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)

    customer = relationship("Customer", back_populates="api_keys")
    usage_logs = relationship("UsageLog", back_populates="api_key")
    device_registrations = relationship("DeviceRegistration", back_populates="api_key", cascade="all, delete-orphan")


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)
    endpoint = Column(String, nullable=False)
    model = Column(String, nullable=True)
    request_count = Column(Integer, default=1)
    cost = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    extra_data = Column(Text, nullable=True)  # JSON string for additional data (renamed from metadata to avoid SQLAlchemy conflict)

    customer = relationship("Customer", back_populates="usage_logs")
    api_key = relationship("APIKey", back_populates="usage_logs")


class PricingConfig(Base):
    __tablename__ = "pricing_config"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False, unique=True, index=True)
    per_request_cost = Column(Float, default=0.0)
    per_model_cost = Column(Float, default=0.0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModelMetadata(Base):
    __tablename__ = "model_metadata"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    context_window = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DeviceRegistration(Base):
    """
    Stores device tokens linked to API keys.
    When a user activates their API key on a device, a device token is generated
    and stored here. The device can then authenticate using just the token.
    """
    __tablename__ = "device_registrations"

    id = Column(Integer, primary_key=True, index=True)
    device_token = Column(String, unique=True, nullable=False, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)
    device_name = Column(String, nullable=True)  # e.g., "iPhone", "Chrome on Windows"
    device_type = Column(String, nullable=True)  # "phone", "computer", "tablet"
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)

    api_key = relationship("APIKey", back_populates="device_registrations")


class ExternalAPIUsage(Base):
    """
    Track external API calls (e.g. Odds API, ESPN).
    """
    __tablename__ = "external_api_usage"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String, nullable=False, index=True) # "odds_api", "espn", "open_meteo"
    endpoint = Column(String, nullable=False) # e.g. "/sports/nfl/odds"
    method = Column(String, default="GET")
    status_code = Column(Integer, nullable=True)
    cost_credits = Column(Integer, default=0) # For Odds API credits
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metadata_json = Column(Text, nullable=True) # Additional context


# Database setup
def get_database_url():
    """Get database URL from environment or use default."""
    return os.getenv("DATABASE_URL", "sqlite:///./data/lmapi.db")


# Create engine
database_url = get_database_url()

# Ensure data directory exists for SQLite with proper permissions
if database_url.startswith("sqlite"):
    # Handle both sqlite:/// and sqlite://// (absolute paths)
    db_path = database_url.replace("sqlite:///", "").replace("sqlite:////", "/")
    # If path doesn't start with /, make it relative to current directory
    if not db_path.startswith("/"):
        db_path = os.path.join(os.getcwd(), db_path)
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
        # Set permissions so user can write (777 for directory to allow container user)
        try:
            os.chmod(db_dir, 0o777)
        except (OSError, PermissionError):
            pass  # Ignore if we can't set permissions

engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database and create all tables."""
    # Ensure data directory exists and is writable before creating tables
    database_url = get_database_url()
    if database_url.startswith("sqlite"):
        # Handle both sqlite:/// and sqlite://// (absolute paths)
        db_path = database_url.replace("sqlite:///", "").replace("sqlite:////", "/")
        # If path doesn't start with /, make it relative to current directory
        if not db_path.startswith("/"):
            db_path = os.path.join(os.getcwd(), db_path)
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
            try:
                os.chmod(db_dir, 0o777)  # Allow container user to write
            except (OSError, PermissionError):
                pass

    Base.metadata.create_all(bind=engine)

    # Ensure database file has correct permissions (if SQLite)
    if database_url.startswith("sqlite"):
        db_path = database_url.replace("sqlite:///", "").replace("sqlite:////", "/")
        if not db_path.startswith("/"):
            db_path = os.path.join(os.getcwd(), db_path)
        if os.path.exists(db_path):
            try:
                # Make database file readable/writable by all (for container user)
                os.chmod(db_path, 0o666)
            except (OSError, PermissionError):
                pass  # Ignore if we can't set permissions


def get_db_session():
    """Get database session (for FastAPI dependency injection)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session_sync():
    """Get database session synchronously (for CLI scripts)."""
    return SessionLocal()
