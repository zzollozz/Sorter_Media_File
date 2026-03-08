import sys
from loguru import logger
from config import LOG_FILE


def setup_logger() -> None:
    logger.remove()
    logger.add(LOG_FILE, level="DEBUG", rotation="10 MB", encoding="utf-8")
    logger.add(sys.stderr, level="CRITICAL")