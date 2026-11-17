"""Application error logging."""
import logging
from logging.handlers import RotatingFileHandler
import os

from prometheus.storage.config import data_dir


def initialize_logging(directory=None):
    logger = logging.getLogger('prometheus')
    path = os.path.abspath(os.path.join(directory or data_dir(), 'prometheus.log'))
    if not any(isinstance(handler, RotatingFileHandler) and handler.baseFilename == path
               for handler in logger.handlers):
        handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
