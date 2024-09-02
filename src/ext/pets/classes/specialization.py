import random
from typing import Optional
from abc import abstractmethod, ABC
from .skill import *


class Specialization(ABC):
    _health: int
    _strength: int
    _dexterity: int
    _intellect: int
    _skills: list[Skill]

    @property
    def health(self) -> int:
        return self._health
    
    @property
    def strength(self) -> int:
        return self._strength
    
    @property
    def dexterity(self) -> int:
        return self._dexterity
    
    @property
    def intellect(self) -> int:
        return self._intellect
    
    @property
    def name(self) -> str:
        return self.__class__.__name__[0]
    
    @property
    def prefix(self) -> str:
        return self.__class__.__name__.lower()
    
    @property
    @abstractmethod
    def main_attr(self) -> str:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def middle_attr(self) -> str:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def lowest_attr(self) -> str:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def avatar(self) -> str: # url
        raise NotImplementedError
    
    def _do_stats_roll(self) -> int:
        rolls = []
        for _ in range(4):
            rolls.append(random.randint(1, 6))
        rolls.sort(reverse=True)
        return sum(rolls[:3])
    
    def _do_health_roll(self) -> int:
        return random.randint(20, 40)

    def generate_stats(self) -> None:
        values = self._get_stats_rolls()
        attributes = [self.main_attr, self.middle_attr, self.lowest_attr]
        for attr, value in zip(attributes, values):
            setattr(Specialization, attr, value)
        setattr(Specialization, '_health', self._do_health_roll())

    def _get_stats_rolls(self) -> list[int]:
        values = [self._do_stats_roll() for _ in range(3)]
        values.sort(reverse=True)
        return values
    
    def add_skills(self, pet: 'Pet') -> None:
        pet._skills = {skill.id: skill for skill in self._skills}

    def __str__(self) -> str:
        return self.prefix


class Warrior(Specialization):
    def __init__(self, with_stats = True):
        super().__init__()
        if with_stats:
            self.generate_stats()
        self._skills = [Rage(), ShieldsUp()]

    @property
    def main_attr(self) -> str:
        return 'strength'
    
    @property
    def middle_attr(self) -> str:
        return 'dexterity'
    
    @property
    def lowest_attr(self) -> str:
        return 'intellect'
    
    @property
    def avatar(self) -> str:
        return ""


class Hunter(Specialization):
    def __init__(self, with_stats = True):
        super().__init__()
        if with_stats:
            self.generate_stats()
        self._skills = [PoisonedArrow(), KnifeThrow()]

    @property
    def main_attr(self) -> str:
        return 'dexterity'
    
    @property
    def middle_attr(self) -> str:
        return 'intellect'
    
    @property
    def lowest_attr(self) -> str:
        return 'strength'
    
    @property
    def avatar(self) -> str:
        return ""


class Mage(Specialization):
    def __init__(self, with_stats = True):
        super().__init__()
        if with_stats:
            self.generate_stats()
        self._skills = [HolyBubble(), ReverseInTime()]

    @property
    def main_attr(self) -> str:
        return 'intellect'
    
    @property
    def middle_attr(self) -> str:
        return 'strength'
    
    @property
    def lowest_attr(self) -> str:
        return 'dexterity'
    
    @property
    def avatar(self) -> str:
        return ""
    

class Demon(Specialization):
    def __init__(self, with_stats = True):
        super().__init__()
        if with_stats:
            self.generate_stats()
        self._skills = []

    @property
    def main_attr(self) -> str:
        return 'intellect'
    
    @property
    def middle_attr(self) -> str:
        return 'dexterity'
    
    @property
    def lowest_attr(self) -> str:
        return 'strength'
    
    @property
    def avatar(self) -> str:
        return ""


class SpecUtils:
    @staticmethod
    def get_random_spec() -> Specialization:
        return random.choice([Warrior, Hunter, Mage])()

    @staticmethod
    def get_spec_by_letter(letter: Optional[str]) -> Optional[Specialization]:
        match letter:
            case "W" | "Wa" | "В" | "Ва":
                return Warrior() 
            case "H" | "Hu" | "О" | "Ох":
                return Hunter()
            case "M" | "Ma" | "М" | "Ма":
                return Mage()
            case _:
                return None
            
    @staticmethod
    def get_spec_by_prefix(prefix: str) -> Optional[Specialization]:
        match prefix:
            case 'warrior':
                return Warrior(with_stats=False)
            case 'hunter':
                return Hunter(with_stats=False)
            case 'mage':
                return Mage(with_stats=False)
            case 'demon':
                return Demon(with_stats=False)
            case _:
                return None

