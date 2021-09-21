import logging


def create_logger(level):
    logger = logging.getLogger('Arctic')
    logger.setLevel(level=logging.getLevelName(level))
    handler = logging.StreamHandler()
    handler.setLevel(level=logging.getLevelName(level))
    handler2 = logging.FileHandler('./core_elements/errors.log')
    handler2.setLevel(logging.ERROR)
    logger.addHandler(handler)
    logger.addHandler(handler2)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    handler2.setFormatter(formatter)
