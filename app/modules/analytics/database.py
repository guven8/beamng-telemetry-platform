"""
Database configuration and session management.

Sets up SQLAlchemy connection to PostgreSQL and provides database session factory.
"""
import os
import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://beamng:beamng@localhost:5432/beamng_telemetry"
)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=False)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency function for FastAPI to get database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def wait_for_db(max_retries=30, retry_delay=1):
    """
    Wait for database to be ready by attempting a connection.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        
    Returns:
        True if database is ready, False otherwise
    """
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
        except OperationalError as e:
            if attempt < max_retries - 1:
                logger.info(f"Database not ready (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Database connection failed after {max_retries} attempts: {e}")
                return False
    return False


def init_db():
    """
    Initialize database tables.
    Creates all tables defined in models.
    
    Must be called after models are imported so they're registered with Base.metadata.
    """
    # Wait for database to be ready
    if not wait_for_db():
        raise Exception("Database not available after retries")
    
    # Import models to ensure they're registered with Base.metadata
    # This must happen before create_all() is called
    from app.modules.analytics.models import Session, TelemetryFrame  # noqa: F401
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")



