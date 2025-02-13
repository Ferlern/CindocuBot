from math import log


FIRST_LVL_EXPERIENCE = 100
LVL_REQUIREMENTS_GROW_PERCENT = 1.1

FIRST_PET_LVL_EXPERIENCE = 40
PET_LVL_REQUIREMENTS_GROW_PERCENT = 1.05


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


def pet_lvl_to_exp(lvl: int) -> int:
    if lvl == 21: lvl = 20 # 20 lvl is the highest
    
    fle = FIRST_PET_LVL_EXPERIENCE
    prc = PET_LVL_REQUIREMENTS_GROW_PERCENT
    return int(fle * (prc ** (lvl - 1) - 1) / (prc - 1))

def format_pet_exp_and_lvl(exp: int, lvl: int):
    required_exp = pet_lvl_to_exp(lvl + 1) - pet_lvl_to_exp(lvl) 
    return(f"**{lvl}** ({exp}/{required_exp})")