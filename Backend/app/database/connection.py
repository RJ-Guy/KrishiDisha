"""
Database Connection, Engine Pooling, and Session Lifecycle Management for KrishiDisha.
Supports production-grade PostgreSQL with automatic zero-configuration SQLite fallback
for seamless local testing and offline hackathon demonstration.
"""

import os
import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

logger = logging.getLogger("krishidisha.database")

# ==========================================
# Shared Declarative Base
# ==========================================
class Base(DeclarativeBase):
    """Declarative Base for all KrishiDisha SQLAlchemy ORM models."""
    pass


# ==========================================
# Connection String Resolution
# ==========================================
DEFAULT_POSTGRES_URL = "postgresql://postgres:postgres@localhost:5432/krishidisha"
DEFAULT_SQLITE_URL = "sqlite:///./krishidisha.db"

# Retrieve from environment variable or default
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)


def _create_database_engine(url: str):
    """
    Creates an engine with appropriate pooling and thread-safety options.
    Falls back gracefully to SQLite if PostgreSQL is unreachable.
    """
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=False,
        )
    
    # PostgreSQL Configuration with Connection Pooling
    try:
        pg_engine = create_engine(
            url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
        )
        # Test connection immediately
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return pg_engine
    except Exception as e:
        logger.warning(
            f"PostgreSQL connection to {url} failed: {e}. Falling back to SQLite local database."
        )
        return create_engine(
            DEFAULT_SQLITE_URL,
            connect_args={"check_same_thread": False},
            echo=False,
        )


# Global Engine Instance
engine = _create_database_engine(DATABASE_URL)

# Thread-safe Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ==========================================
# FastAPI Session Dependency
# ==========================================
def get_db() -> Generator[Session, None, None]:
    """
    Canonical FastAPI database session dependency.
    Yields a scoped session and guarantees connection closure/cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_relationships():
    """Ensure bi-directional relationship mapping between Buyer and Offer."""
    try:
        from app.models.buyer import Buyer
        from sqlalchemy.orm import relationship
        if not hasattr(Buyer, "offers"):
            Buyer.offers = relationship("Offer", back_populates="buyer")
    except Exception:
        pass


# Run relationship configuration on module import
_ensure_relationships()


# ==========================================
# Database Initialization & Health Check
# ==========================================
def init_db() -> None:
    """
    Initializes all 17+ core database tables registered on Base.metadata.
    Imports app.models to ensure complete entity registration before creation.
    """
    try:
        # Import models to register them on Base.metadata
        import app.models  # noqa: F401
        _ensure_relationships()

        Base.metadata.create_all(bind=engine)
        logger.info("All KrishiDisha database tables verified/created successfully.")
    except Exception as e:
        logger.error(f"Error initializing database tables: {e}")
        raise e


def check_connection() -> bool:
    """Verifies active connectivity to the underlying database."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
