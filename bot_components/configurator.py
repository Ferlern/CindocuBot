import json
from typing import TypedDict


class Warn(TypedDict):
    text: str
    mute_time: int
    ban: bool


class Personal_voice(TypedDict):
    categoty: int
    price: int
    slot_price: int
    bitrate_price: int


class System(TypedDict):
    token: str
    initial_extensions: list[str]


class Experience_system(TypedDict):
    experience_channel: int
    cooldown: int
    minimal_message_length: int
    experience_per_message: list[int]
    roles: dict[str, int]
    coins_per_level_up: int


class Additional_emoji(TypedDict):
    heart: str


class Config(TypedDict):
    guild: int
    token: str
    prefixes: list[str]
    mute_role: int
    suggestions_channel: int
    moderators_roles: list[int]
    warns_system: list[Warn]
    coin: str
    daily: int
    marry_price: int
    personal_voice: Personal_voice
    experience_system: Experience_system
    additional_emoji: Additional_emoji


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
