import os
import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

logger = logging.getLogger("powerflex.database")

# Load .env file if it exists (project root)
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass  # python-dotenv not installed; rely on OS env only

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://localhost:5432/powerflex",
)

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_engine():
    return engine


def get_session():
    return SessionLocal()


def init_db():
    """Create all tables defined by Base metadata."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created (if not exists)")


def check_connection():
    """Verify database connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        return True
    except Exception as e:
        logger.warning("Database connection failed: %s", e)
        return False
