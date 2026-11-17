import logging
from prometheus.storage.log import initialize_logging


def test_logging_writes_and_does_not_duplicate_handler(tmp_path):
    logger = initialize_logging(str(tmp_path))
    count = len(logger.handlers)
    assert initialize_logging(str(tmp_path)) is logger
    assert len(logger.handlers) == count
    logger.error('test log entry')
    for handler in logger.handlers:
        handler.flush()
    assert 'test log entry' in (tmp_path / 'prometheus.log').read_text()
    for handler in logger.handlers[:]:
        if getattr(handler, 'baseFilename', None) == str(tmp_path / 'prometheus.log'):
            logger.removeHandler(handler)
            handler.close()
