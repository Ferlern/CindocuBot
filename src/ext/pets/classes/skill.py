from __future__ import annotations
from typing import TYPE_CHECKING
from abc import abstractmethod, ABC

from disnake import Embed
from src.ext.pets.utils import GameEmbed
from src.translation import get_translator


t = get_translator(route='ext.pet_battle')


if TYPE_CHECKING:
    from .pet import Pet

class Skill(ABC):
    def __init__(
        self,
        id: str,
        name: str,
        affects: dict[str, int],
        cooldown: int | None
    ) -> None:
        self._id = id
        self._name = name
        self._affects = affects
        self._cooldown = cooldown
        
        self._journal_desc: str
        self._current_cooldown: int | None = 0

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def cooldown(self) -> int | None:
        return self._cooldown
    
    @property
    def journal_desc(self) -> str:
        return self._journal_desc
    
    def apply(self, attacker: Pet, **kwargs) -> bool:
        if not self.usable:
            return False
        
        for attr, value in self._affects.items():
            attacker.status_effects[attr] = value
        self._start_cooldown()
        return True

    @property
    def usable(self) -> bool:
        return self._current_cooldown == 0
    
    def _start_cooldown(self) -> None:
        self._current_cooldown = self._cooldown
    
    def update_cooldown(self) -> None:
        if not self._current_cooldown:
            return
        
        self._current_cooldown = max(
            0, self._current_cooldown - 1)
        
    def skill_showcase(self) -> Embed:
        is_usable = {
            True: t("yes_"),
            False: t("no_")
        }

        desc = t("is_usable", usability=is_usable[self.usable])

        if self._current_cooldown != 0:
            if self._cooldown:
                cooldown = self._current_cooldown
                desc += t("before_use", count=cooldown)
        
        else:
            cooldown = (t("cooldown_", count=self._cooldown)
                if self._cooldown else t("only_once_per_game"))
            desc += t("cooldown_info", info=cooldown)

        embed = GameEmbed(
            title = self.name,
            description = desc
        )
        embed.add_field(
            name=t("cooldown_description"),
            value=self.skill_description,
            inline=False
        )
        embed.set_thumbnail(self.skill_icon)
        return embed
    
    @property
    @abstractmethod
    def skill_description(self) -> str:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def skill_icon(self) -> str: # url
        raise NotImplementedError
    

class HolyBubble(Skill):
    def __init__(self) -> None:
        super().__init__(
            id = "s1",
            name = "Holy Potion",
            affects = {"in_bubble": 999},
            cooldown = 4
        )

        self._journal_desc = t("bubble_journal_desc")

    @property
    def skill_description(self) -> str:
        return t("bubble_desc")
    
    @property
    def skill_icon(self) -> str:
        return "https://imgur.com/xurSEn0.jpg"


class ReverseInTime(Skill):
    def __init__(self) -> None:
        super().__init__(
            id = "s2",
            name = "Reverse in Time",
            affects = {"reversed_in_time": 1},
            cooldown = None
        )

    @property
    def skill_description(self) -> str:
        return t("reverse_desc")
    
    @property
    def skill_icon(self) -> str:
        return "https://imgur.com/K90Covt.jpg"

    def apply(self, attacker: Pet, **kwargs) -> bool:
        if not self.usable:
            return False
        attacker.reverse_last_hp()
        self._journal_desc = t("reverse_journal_desc")
        self._start_cooldown()
        return True


class Rage(Skill):
    def __init__(self) -> None:
        super().__init__(
            id = "s3",
            name = "Rage",
            affects = {"in_rage": 2},
            cooldown = 2
        )

        self._journal_desc = t("rage_journal_desc")

    @property
    def skill_description(self) -> str:
        return t("rage_desc")
    
    @property
    def skill_icon(self) -> str:
        return "https://imgur.com/R6LIf8m.jpg"


class ShieldsUp(Skill):
    def __init__(self) -> None:
        super().__init__(
            id = "s4",
            name = "Shields Up",
            affects = {"under_shield": 2},
            cooldown = 3
        )


    @property
    def skill_description(self) -> str:
        return t("shield_desc")
    
    @property
    def skill_icon(self) -> str:
        return "https://imgur.com/ozbLSaV.jpg"
    
    def apply(self, attacker: Pet, **kwargs) -> bool:
        if not self.usable:
            return False
        
        for attr, value in self._affects.items():
            attacker.status_effects[attr] = value
        self._start_cooldown()
        reduction = attacker.calculate_damage_reduction()
        self._journal_desc = t("shield_journal_desc", reduction=reduction)
        return True


class PoisonedArrow(Skill):
    def __init__(self) -> None:
        super().__init__(
            id = "s5",
            name = "Poisoned Arrow",
            affects = {"poisoned": 2},
            cooldown = 5
        )

    @property
    def skill_description(self) -> str:
        return t("arrow_desc")
    
    @property
    def skill_icon(self) -> str:
        return "https://imgur.com/JEJeUip.jpg"
    
    def apply(self, attacker: Pet, defender: Pet, damage: int, **kwargs) -> bool:
        if not self.usable:
            return False

        defender.poison_damage = damage
        for attr, value in self._affects.items():
            defender.status_effects[attr] = value
        self._start_cooldown()
        self._journal_desc = t("arrow_journal_desc", damage=damage)
        return True


class KnifeThrow(Skill):
    def __init__(self) -> None:
        super().__init__(
            id = "s6",
            name = "Knife Throw",
            affects = {"extra_knife": 1},
            cooldown = None
        )

    @property
    def skill_description(self) -> str:
        return t("knife_desc")
    
    @property
    def skill_icon(self) -> str:
        return "https://imgur.com/5XGfzgL.jpg"

    def apply(
        self, turn: int,
        attacker: Pet, defender: Pet,
        damage: int
    ) -> bool:
        if not self.usable:
            return False
        
        attacker.attack_target(defender, damage)
        if damage:
            self._journal_desc = t("knife_journal_desc_success", damage=damage)
        else:
            self._journal_desc = t("knife_journal_desc_failure")
        self._start_cooldown()
        return True