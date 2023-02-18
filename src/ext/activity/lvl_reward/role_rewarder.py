from typing import Optional

import asyncio
import disnake

from src.logger import get_logger
from src.database.models import ExperienceSettings, Members
from src.translation import get_translator


logger = get_logger()
t = get_translator(route="ext.activity")


async def remove_outdated_roles(outdated_experiece_roles_ids, member):
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


async def add_new_role(expected_role_id, member_experiece_roles_ids, member):
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

    int_lvl_keys = (int(lvl_key) for lvl_key in roles.keys())
    expected_role_id = max(int(lvl_key) for lvl_key in int_lvl_keys if int(lvl_key) <= lvl)

    experiece_roles_ids = set(roles.values())
    member_roles_ids = {role.id for role in member.roles}
    member_experiece_roles_ids = experiece_roles_ids & member_roles_ids
    outdated_experiece_roles_ids = member_experiece_roles_ids - {expected_role_id}

    await asyncio.gather(
        remove_outdated_roles(outdated_experiece_roles_ids, member), 
        add_new_role(expected_role_id, member_experiece_roles_ids, member)
    )

    if expected_role_id in member_experiece_roles_ids:
        return t('award_role', role_id=expected_role_id) 
