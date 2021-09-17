import logging


def create_logger(level):
    logger = logging.getLogger('Arctic')
    logger.setLevel(level=logging.getLevelName(level))
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
