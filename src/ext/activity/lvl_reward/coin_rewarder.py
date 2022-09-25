from typing import Optional

import disnake
from src.logger import get_logger
from src.database.models import ExperienceSettings, Members
from src.ext.economy.services import get_economy_settings


logger = get_logger()


async def coin_rewarder(
    member: disnake.Member,
    member_data: Members,
    settings: ExperienceSettings,
    lvl: int,
) -> Optional[str]:
    award_amount = settings.coins_per_level_up * lvl + 100
    member_data.balance += award_amount  # type: ignore
    economy_settings = get_economy_settings(member.guild.id)

    logger.info(
        "give %d money to member %s on guild %s (lvl|reward)",
        award_amount,
        member,
        member.guild,
    )

    return f"{award_amount} {economy_settings.coin}"
