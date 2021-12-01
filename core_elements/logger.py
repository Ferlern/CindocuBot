import logging
from logging.handlers import RotatingFileHandler


formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def create_logger(level):
    logger = logging.getLogger('Arctic')
    logger.setLevel(level=logging.getLevelName(level))
    
    handler = logging.StreamHandler()
    handler.setLevel(level=logging.getLevelName(level))
    
    handler2 = logging.FileHandler('./core_elements/errors.log')
    handler2.setLevel(logging.ERROR)
    
    logger.addHandler(handler)
    logger.addHandler(handler2)
    
    handler.setFormatter(formatter)
    handler2.setFormatter(formatter)
    
    create_voice_logger()
    
def create_voice_logger():
    voice_logger = logging.getLogger('Arctic-voice')
    voice_logger.setLevel('DEBUG')
    
    voice_handler = RotatingFileHandler('./core_elements/voice.log', mode='a',
                                        maxBytes=1024*1024, backupCount=3,
                                        encoding=None, delay=0)
    voice_handler2 = logging.FileHandler('./core_elements/voice_errors.log')
    voice_handler3 = logging.StreamHandler()
    
    voice_handler.setFormatter(formatter)
    voice_handler2.setFormatter(formatter)
    voice_handler3.setFormatter(formatter)
    
    voice_handler2.setLevel(logging.WARNING)
    voice_handler3.setLevel(logging.DEBUG)
    
    voice_logger.addHandler(voice_handler)
    voice_logger.addHandler(voice_handler2)
    voice_logger.addHandler(voice_handler3)