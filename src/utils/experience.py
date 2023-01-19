from math import log


FIRST_LVL_EXPERIENCE = 100
LVL_REQUIREMENTS_GROW_PERCENT = 1.1


def exp_to_lvl(exp: int) -> int:
    fle = FIRST_LVL_EXPERIENCE
    prc = LVL_REQUIREMENTS_GROW_PERCENT
    return int(log(exp / fle * (prc - 1) + 1, prc) + 1)


def lvl_to_exp(lvl: int) -> int:
    fle = FIRST_LVL_EXPERIENCE
    prc = LVL_REQUIREMENTS_GROW_PERCENT
    return int(fle * (prc ** (lvl - 1) - 1) / (prc - 1))


def format_exp(exp: int) -> str:
    current_lvl = exp_to_lvl(exp)
    lvl_require = lvl_to_exp(current_lvl)
    next_lvl_require = lvl_to_exp(current_lvl + 1)
    return (f"**{current_lvl}** ({exp - lvl_require}/"
            f"{next_lvl_require - lvl_require})")
