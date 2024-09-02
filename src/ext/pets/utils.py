from disnake import MessageCommandInteraction, Embed
from typing import Optional

from src.discord_views.shortcuts import ModalInput, request_data_via_modal
from src.translation import get_translator
from src.database.models import Pets


t = get_translator(route='ext.pets')


# def profile_creator(pet: Pets):
#     font = ImageFont.truetype("arial.ttf", 25)
#     image = Image.open(requests.get("link", stream=True).raw)
#     drawer = ImageDraw.Draw(image)
#     drawer.text((50, 100), "TestText", fill='black', font=font)

#     image.save('new_img.jpg')
#     image.show()


async def delete_pet_confirmation(interaction: MessageCommandInteraction) -> Optional[str]:
    confirmation_field = ModalInput(
        label=t("delete_confirm"),
        max_length=11,
        placeholder=t("delete_placeholder")
    )
    try:
        modal_data = await request_data_via_modal(
            inter = interaction,
            title = t("confirmation"),
            fields = confirmation_field
        )
        data = modal_data[1]
    except:
        data = None
    return data


async def rename_pet_request(interaction: MessageCommandInteraction) -> Optional[str]:
    name_input = ModalInput(
        label=t("new_name"),
        max_length=25,
    )
    try:
        modal_data = await request_data_via_modal(
            inter = interaction,
            title = t("rename"),
            fields = name_input
        )
        data = modal_data[1]
    except:
        data = None
    return data


async def auc_pet_price_request(interaction: MessageCommandInteraction) -> Optional[str]:
    price_input = ModalInput(
        label=t("pet_price"),
        max_length=7
    )
    try:
        modal_data = await request_data_via_modal(
            inter = interaction,
            title = t("pet_auction"),
            fields = price_input
        )
        data = modal_data[1]
    except:
        data = None
    return data


class GameEmbed(Embed):
    def __init__(self, **kwargs) -> None:
        super().__init__(
            color = 0xff0000,
            **kwargs
        )


def exp_display(current, max_experience, width=15) -> str:
    filled_length = int(width * current // max_experience)
    empty_length = width - filled_length
    
    bar = '█' * filled_length + '░' * empty_length
    return f'{current}/{max_experience} | [{bar}]'
