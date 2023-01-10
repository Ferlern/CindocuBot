from typing import Any

import i18n

from src.logger import get_logger


logger = get_logger()


i18n.load_path.append('./locales')
i18n.set("locale", "ru")
i18n.set("fallback", "ru")
i18n.set("enable_memoization", True)


def get_translator(*, route="general"):
    def translator(key: str, **kwargs: Any) -> str:
        key = f"{route}.{key}" if route else key
        logger.debug('translator called with key "%s" and kwargs: %s',
                     key, kwargs)
        return i18n.t(key, **kwargs)
    return translator


def _determine_plural_form(*, count=1):
    count = abs(count)
    if count % 10 >= 5 or count % 10 == 0 or (count % 100) in range(11, 20):
        return 2
    if count % 10 == 1:
        return 0
    return 1


i18n.add_function("p", _determine_plural_form)
