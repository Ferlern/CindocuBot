import logging
from logging.handlers import RotatingFileHandler

from src import settings

_formatter = logging.Formatter(u'[%(asctime)s:%(name)s] - %(levelname)s in %(module)s#%(lineno)d: %(message)s')  # noqa: E501
PATH = settings.LOGS_PATH


def get_logger():
    return logging.getLogger(settings.APP_NAME)


def get_voice_logger():
    return logging.getLogger(f'{settings.APP_NAME}-voice')


def _create_logger():
    level = logging.DEBUG if settings.DEBUG else logging.INFO

    logger = logging.getLogger(settings.APP_NAME)
    logger.setLevel(level=level)

    handler = logging.StreamHandler()
    handler.setLevel(level=level)

    handler2 = logging.FileHandler(f'{PATH}/errors.log',
                                   encoding='UTF-8')
    handler2.setLevel(logging.ERROR)

    logger.addHandler(handler)
    logger.addHandler(handler2)

    handler.setFormatter(_formatter)
    handler2.setFormatter(_formatter)


def _create_voice_logger():
    voice_logger = logging.getLogger(f'{settings.APP_NAME}-voice')
    voice_logger.setLevel('DEBUG')

    voice_handler = RotatingFileHandler(f'{PATH}/voice.log',
                                        mode='a',
                                        maxBytes=1024 * 1024, backupCount=3,
                                        encoding='UTF-8', delay=False)
    voice_handler2 = logging.FileHandler(f'{PATH}/voice_errors.log',
                                         encoding='UTF-8')
    voice_handler3 = logging.StreamHandler()

    voice_handler.setFormatter(_formatter)
    voice_handler2.setFormatter(_formatter)
    voice_handler3.setFormatter(_formatter)

    voice_handler2.setLevel(logging.WARNING)
    voice_handler3.setLevel(logging.DEBUG)

    voice_logger.addHandler(voice_handler)
    voice_logger.addHandler(voice_handler2)
    voice_logger.addHandler(voice_handler3)


def setup_logger():
    _create_logger()
    _create_voice_logger()
