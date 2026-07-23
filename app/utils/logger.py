from pathlib import Path
from loguru import logger
import sys


def setup_logger(log_path: str = "data/output/app.log"):
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(log_path, level="INFO", rotation="1 MB", retention=5)
    return logger
