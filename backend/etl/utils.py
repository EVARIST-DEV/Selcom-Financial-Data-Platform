# backend/etl/utils.py
import os
import sys
from contextlib import contextmanager
from loguru import logger
import psycopg2
from psycopg2.extras import DictCursor

# Configure Loguru to write to both console and rotation files
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=os.getenv("LOG_LEVEL", "INFO"),
)
logger.add(
    "logs/etl_pipeline.log",
    rotation="50 MB",
    retention="10 days",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
)

@contextmanager
def get_raw_connection():
    """Provides a raw psycopg2 connection context for high-performance bulk copies."""
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/selcom_db")
    conn = None
    try:
        conn = psycopg2.connect(db_url)
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database transaction rolled back due to error: {e}")
        raise e
    finally:
        if conn:
            conn.close()