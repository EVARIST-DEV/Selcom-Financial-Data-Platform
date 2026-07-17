import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from loguru import logger

load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "selcom_db")

DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():
    """
    FastAPI dependency that provides a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    """
    Verify the PostgreSQL connection.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.success("Connected to PostgreSQL successfully.")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def init_db_schema():
    """
    Reads backend/database/schema.sql and executes it using the 
    SQLAlchemy engine to prepare tables and indexes.
    """
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    
    if not os.path.exists(schema_path):
        logger.error(f"Initialization schema missing at expected path: {schema_path}")
        return False

    logger.info("Initializing SelFlow PaySim Warehouse schema...")
    try:
        with open(schema_path, "r") as f:
            sql_script = f.read()

        # SQLAlchemy v2 requires wrapping raw text queries inside text()
        # and executing inside an active transaction block.
        with engine.begin() as connection:
            connection.execute(text(sql_script))
            
        logger.success("Database tables and indexes verified/created successfully.")
        return True
    except Exception as e:
        logger.critical(f"Failed to initialize database schema: {e}")
        raise e