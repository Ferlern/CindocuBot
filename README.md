# CindocuBot

Дискорд бот для сервера [Cindocu](https://discord.gg/4ZVhkXxnUK)

## Описание

TODO: дополнить раздел

## Запуск

### Автоматически

- Установить [Docker](https://www.docker.com/products/docker-desktop/)
- `git clone https://github.com/Ferlern/CindocuBot.git & cd CindocuBot`
- `docker-compose up -d`

### Вручную

- Установить [Poetry](https://www.jetbrains.com/help/pycharm/poetry.html)
- Установить [Postgresql](https://www.postgresql.org/download/)
- `git clone https://github.com/Ferlern/CindocuBot.git & cd CindocuBot`
- Установить зависимости `poetry install`
- Подготовить БД `python setup.py`
- Запустить бота `python run.py`

## Настройки

### Глобальные

- [settings.py](https://github.com/Ferlern/CindocuBot/blob/main/src/settings.py) содержит настройки бота. Желательно установить хотя бы один IMAGE_CHANNEL, иначе некоторые функции не будут работать.
- [translation.py](https://github.com/Ferlern/CindocuBot/blob/main/src/translation.py) содержит настройки локализации. Локаль по умолчанию изменяется там.
- [logger.py](https://github.com/Ferlern/CindocuBot/blob/main/src/logger.py) содержит настройки логгера.

### Для гильдий

Многие системы бота могут быть настроены для каждой гильдии отдельно. На данный момент настройка возможна только с помощью SQL. Подробнее о возможных настройках можно почитать в документации к моделям в [models.py](https://github.com/Ferlern/CindocuBot/blob/main/src/database/models.py)
