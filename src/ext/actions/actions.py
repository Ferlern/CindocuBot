import disnake

from src.translation import get_translator
from src.ext.fun.categories import Categories


t = get_translator(route='general')


def get_resctictable_action() -> dict[str, str]:
    actions = {t('all_actions'): 'all'}
    for cat in Categories:
        actions[cat.get_translated_name()] = cat.value
    return actions


def is_action_restricted(
    action_name: str,
    action_author: disnake.Member,
    target_restrictions: dict[str, list[str]],
) -> bool:
    role_ids = {str(role.id) for role in action_author.roles}
    member_restrictions = target_restrictions.get(str(action_author.id))
    if member_restrictions and (action_name in member_restrictions or 'all' in member_restrictions):
        return True

    actual_role_restriction_keys = set(target_restrictions) & role_ids
    for key in actual_role_restriction_keys:
        role_restrictions = target_restrictions.get(key)
        if role_restrictions and (action_name in role_restrictions or 'all' in role_restrictions):
            return True

    return False
