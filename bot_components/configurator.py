import json
from typing import TypedDict
from .bot_emoji import AdditionalEmoji


class Warn(TypedDict):
    text: str
    mute_time: int
    ban: bool


class PersonalVoice(TypedDict):
    categoty: int
    price: int
    slot_price: int
    bitrate_price: int


class System(TypedDict):
    token: str
    initial_extensions: list[str]


class ExperienceSystem(TypedDict):
    experience_channel: int
    cooldown: int
    minimal_message_length: int
    experience_per_message: list[int]
    roles: dict[str, int]
    coins_per_level_up: int
    

class AutoTranslation(TypedDict):
    channels: list
    lang: str


class Config(TypedDict):
    guild: int
    token: str
    prefixes: list[str]
    commands_channels: list[int]
    mute_role: int
    suggestions_channel: int
    moderators_roles: list[int]
    warns_system: list[Warn]
    coin: str
    daily: int
    marry_price: int
    personal_voice: PersonalVoice
    experience_system: ExperienceSystem
    auto_translation: AutoTranslation
    additional_emoji: AdditionalEmoji


class Configurator:
    def __init__(self) -> None:
        self.system: System
        self.config: Config

    def dump(self):
        with open("./bot_components/config.json", "w") as write_file:
            to_dump = [self.system, self.config]
            json.dump(to_dump, write_file, indent=4)

    def load(self):
        with open("./bot_components/config.json", "r") as write_file:
            data = json.load(write_file)
            self.system = System(data[0])
            self.config = Config(data[1])

    def reload(self):
        self.dump()
        self.load()


configurator = Configurator()
configurator.load()
