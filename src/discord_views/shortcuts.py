from typing import Any, Optional, Union, TypeVar, Generic, overload
import os

import disnake
from disnake.ext import commands
from disnake.ext.commands.converter import run_converters

from src.custom_errors import RegularException
from src.discord_views.base_view import BaseModal
from src.converters import translate_converter_error


Output = TypeVar('Output')
F1 = TypeVar('F1')
F2 = TypeVar('F2')
F3 = TypeVar('F3')
F4 = TypeVar('F4')
F5 = TypeVar('F5')


class ModalInput(disnake.ui.TextInput, Generic[Output]):
    def __init__(
        self,
        type_: type[Output] = str,
        /,
        converter=None,
        *,
        label: str,
        style: disnake.TextInputStyle = disnake.TextInputStyle.short,
        placeholder: Optional[str] = None,
        value: Optional[str] = None,
        required: bool = True,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
    ) -> None:
        self.converter = converter or type_
        super().__init__(
            label=label,
            custom_id=os.urandom(16).hex(),
            style=style,
            placeholder=placeholder,
            value=value,
            required=required,
            min_length=min_length,
            max_length=max_length,
        )


@overload
async def request_data_via_modal(
    inter: Union[disnake.ApplicationCommandInteraction, disnake.MessageCommandInteraction],
    title: str,
    fields: ModalInput[F1],
) -> tuple[disnake.ModalInteraction, F1]: ...


@overload
async def request_data_via_modal(
    inter: Union[disnake.ApplicationCommandInteraction, disnake.MessageCommandInteraction],
    title: str,
    fields: tuple[ModalInput[F1]],
) -> tuple[disnake.ModalInteraction, F1]: ...


@overload
async def request_data_via_modal(
    inter: Union[disnake.ApplicationCommandInteraction, disnake.MessageCommandInteraction],
    title: str,
    fields: tuple[ModalInput[F1], ModalInput[F2]],
) -> tuple[disnake.ModalInteraction, F1, F2]: ...


@overload
async def request_data_via_modal(
    inter: Union[disnake.ApplicationCommandInteraction, disnake.MessageCommandInteraction],
    title: str,
    fields: tuple[ModalInput[F1], ModalInput[F2], ModalInput[F3]],
) -> tuple[disnake.ModalInteraction, F1, F2, F3]: ...


@overload
async def request_data_via_modal(
    inter: Union[disnake.ApplicationCommandInteraction, disnake.MessageCommandInteraction],
    title: str,
    fields: tuple[ModalInput[F1], ModalInput[F2], ModalInput[F3], ModalInput[F4]],
) -> tuple[disnake.ModalInteraction, F1, F2, F3, F4]: ...


@overload
async def request_data_via_modal(
    inter: Union[disnake.ApplicationCommandInteraction, disnake.MessageCommandInteraction],
    title: str,
    fields: tuple[ModalInput[F1], ModalInput[F2], ModalInput[F3], ModalInput[F4], ModalInput[F5]],
) -> tuple[disnake.ModalInteraction, F1, F2, F3, F4, F5]: ...


async def request_data_via_modal(
    inter: Union[disnake.ApplicationCommandInteraction, disnake.MessageCommandInteraction],
    title: str,
    fields: Union[ModalInput, tuple[ModalInput, ...]],
) -> Any:
    if not isinstance(fields, tuple):
        fields = (fields, )
    bot = inter.bot

    modal = BaseModal(title=title, components=fields)
    await inter.response.send_modal(modal)
    modal_inter = await bot.wait_for(
        "modal_submit",
        check=lambda m: m.custom_id == modal.custom_id,
        timeout=600,
    )
    # This is required for the global error handler.
    inter.response = modal_inter.response

    values = modal_inter.text_values
    result = []
    for idx, field in enumerate(fields, 1):
        param = type('param', tuple(), {'name': str(idx)})
        value = values[field.custom_id]
        try:
            converted_value = await run_converters(
                inter, field.converter, value, param  # type: ignore
            )
        except commands.BadArgument as error:
            error_text = translate_converter_error(error, value, field.converter)
            raise RegularException(error_text) from error
        result.append(converted_value)
    result.insert(0, modal_inter)
    return tuple(result)
