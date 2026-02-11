"""Configuration du système de logs avec rotation."""

import logging
from logging.handlers import RotatingFileHandler
import os

from alita.config import Config


def setup_logger(name: str = "alita") -> logging.Logger:
    """Configure et retourne le logger principal.

    - Fichier avec rotation (max 10MB, 5 backups)
    - Sortie console
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, Config.LOG_LEVEL, logging.INFO))

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler fichier avec rotation
    log_dir = "/app/logs"
    os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "alita.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Logger global
logger = setup_logger()
