from typing import Optional, Iterable

import asyncio
import disnake

from src.logger import get_logger
from src.database.models import ExperienceSettings, Members
from src.translation import get_translator


logger = get_logger()
t = get_translator(route="ext.activity")


async def remove_outdated_roles(
    outdated_experiece_roles_ids: Iterable[int],
    member: disnake.Member,
) -> None:
    if not outdated_experiece_roles_ids:
        return
    outdated_experiece_roles = [
        disnake.Object(role_id) for role_id in outdated_experiece_roles_ids
    ]
    logger.info(
        "remove roles with ids %s from member %s on guild %s (lvl|outdated)",
        outdated_experiece_roles_ids,
        member,
        member.guild,
    )
    await member.remove_roles(*outdated_experiece_roles)


async def add_new_role(
    expected_role_id: int,
    member_experiece_roles_ids: Iterable[int],
    member: disnake.Member,
) -> None:
    if expected_role_id in member_experiece_roles_ids:
        return
    new_role = disnake.Object(expected_role_id)
    logger.info(
        "add role with id %d to member %s on guild %s (lvl|reward)",
        expected_role_id,
        member,
        member.guild,
    )
    await member.add_roles(new_role)


async def role_rewarder(
    member: disnake.Member,
    _: Members,
    settings: ExperienceSettings,
    lvl: int,
) -> Optional[str]:
    roles = settings.roles
    if not roles:
        return

    experience_roles_keys = [lvl_key for lvl_key in roles if int(lvl_key) <= lvl]
    if len(experience_roles_keys) == 0:
        return

    expected_role_id = roles[(max(experience_roles_keys, key=int))]
    experiece_roles_ids = set(roles.values())
    member_roles_ids = {role.id for role in member.roles}
    member_experiece_roles_ids = experiece_roles_ids & member_roles_ids
    outdated_experiece_roles_ids = member_experiece_roles_ids - {expected_role_id}

    expected_role = member.guild.get_role(expected_role_id)
    if expected_role is None:
        return

    await asyncio.gather(
        remove_outdated_roles(outdated_experiece_roles_ids, member),
        add_new_role(expected_role_id, member_experiece_roles_ids, member)
    )

    if expected_role_id not in member_experiece_roles_ids:
        return t('award_role', role_id=expected_role_id)
