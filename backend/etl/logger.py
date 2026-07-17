import os
import sys
from loguru import logger

# Generate log directory relative to etl/
LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Clear out any noisy defaults
logger.remove()

# Console handler
logger.add(
    sys.stdout,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    level="INFO",
    colorize=True,
    enqueue=True,  # Safe for async execution
)

# File auditing handler
logger.add(
    os.path.join(LOGS_DIR, "etl_pipeline.log"),
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    enqueue=True,
)

__all__ = ["logger"]