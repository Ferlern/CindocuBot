from typing import Optional

import disnake

from src.logger import get_logger
from src.database.models import ExperienceSettings, Members
from src.translation import get_translator


logger = get_logger()
t = get_translator(route="ext.activity")


async def role_rewarder(
    member: disnake.Member,
    _: Members,
    settings: ExperienceSettings,
    lvl: int,
) -> Optional[str]:
    roles = settings.roles
    if not roles:
        return

    new_role_id = roles.get(str(lvl))
    if not new_role_id:
        return

    experiece_roles_ids = set(roles.values())
    member_roles_ids = {role.id for role in member.roles}
    member_experiece_roles_ids = experiece_roles_ids & member_roles_ids
    outdated_experiece_roles_ids = member_experiece_roles_ids - {new_role_id}
    outdated_experiece_roles = [
        disnake.Object(role_id) for role_id in outdated_experiece_roles_ids
    ]
    new_role = disnake.Object(new_role_id)

    logger.info(
        "remove roles with ids %s from member %s on guild %s (lvl|outdated)",
        outdated_experiece_roles_ids,
        member,
        member.guild,
    )
    logger.info(
        "add role with id %d to member %s on guild %s (lvl|reward)",
        new_role_id,
        member,
        member.guild,
    )

    await member.add_roles(new_role)
    await member.remove_roles(*outdated_experiece_roles)

    return t('award_role', role_id=new_role_id)
