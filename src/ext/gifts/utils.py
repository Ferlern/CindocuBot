from disnake import MessageCommandInteraction
from typing import Optional

from src.discord_views.shortcuts import ModalInput, request_data_via_modal
from src.translation import get_translator


t = get_translator(route='ext.gifts')


async def request_def_pets_data(interaction: MessageCommandInteraction) -> Optional[str]:
    name_input = ModalInput(
        label=t("pet_name"),
        max_length=25
    )
    try:
        modal_data = await request_data_via_modal(
            inter = interaction,
            title = t("default_pet"),
            fields = name_input
        )
        data = modal_data[1]
    except:
        data = None
    return data


async def request_leg_pets_data(interaction: MessageCommandInteraction) -> Optional[tuple[str, str]]:
    name_input = ModalInput(
        label=t("pet_name"),
        max_length=25,
    )
    spec_input = ModalInput(
        label=t("spec"),
        max_length=2,
        placeholder=t('spec_placeholder')
    )
    try:
        modal_data = await request_data_via_modal(
            inter = interaction,
            title = t("legendary_pet"),
            fields = (name_input, spec_input)
        )
        data = (modal_data[1], modal_data[2])
    except:
        data = None
    return data