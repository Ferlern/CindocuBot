from typing import Optional
import disnake
from disnake.ext import commands
from peewee import DoesNotExist, InternalError

from src.bot import SEBot
from src.translation import get_translator
from src.converters import not_bot_member
from src.custom_errors import UsedNotOnGuild
from src.utils.slash_shortcuts import only_admin
from src.ext.economy.services import (add_shop_role, change_balance,
                                      delete_shop_role, get_economy_settings, CurrencyType)
from src.ext.history.services import make_history


t = get_translator(route="ext.economy")


class EconomyControlCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot

    @commands.slash_command(**only_admin)
    async def add_role(self,
                       inter: disnake.ApplicationCommandInteraction,
                       role: disnake.Role,
                       price: commands.Range[1, ...],
                       ) -> None:
        """
        Добавить роль в магазин ролей

        Parameters
        ----------
        role: Роль, которая будет добавлена
        price: Цена роль в валюте сервера
        """
        guild = inter.guild
        if not guild:
            raise UsedNotOnGuild()

        role_id = role.id
        coin = get_economy_settings(guild.id).coin
        try:
            add_shop_role(
                guild.id,
                role_id=role_id,
                price=price,
            )
        except InternalError:
            await inter.response.send_message(
                t('role_already_added'),
                ephemeral=True,
            )
            return
        await inter.response.send_message(
            t(
                'role_added_to_shop',
                role_id=role_id,
                price=price,
                coin=coin,
            ),
            ephemeral=True,
        )

    @commands.slash_command(**only_admin)
    async def remove_role(
        self,
        inter: disnake.ApplicationCommandInteraction,
        role: disnake.Role,
        role_id: Optional[int] = None,
    ) -> None:
        """
        Убрать роль из магазина ролей

        Parameters
        ----------
        role: Роль, которая будет убрана
        role_id: Роль с этим ID будет удалена, заменяет аргумент role
        """
        guild = inter.guild
        if not guild:
            raise UsedNotOnGuild()

        role_id = role_id or role.id

        try:
            delete_shop_role(
                guild.id,
                role_id=role_id,
            )
        except DoesNotExist:
            await inter.response.send_message(
                t('role_not_found'),
                ephemeral=True,
            )
            return
        await inter.response.send_message(
            t('role_deleted_from_shop'),
            ephemeral=True,
        )

    @commands.slash_command(**only_admin)
    async def change_balance(
        self,
        inter: disnake.ApplicationCommandInteraction,
        currency: CurrencyType = CurrencyType.COIN,
        member=commands.Param(converter=not_bot_member),
        amount: int = commands.Param(),
    ) -> None:
        """
        Изменить баланс пользователя

        Parameters
        ----------
        currency: Валюта
        member: Пользователь, баланс которого будет изменён
        amount: Количество валюты. Может быть отрицательным,\
        но не привышать текущий баланс пользователя
        """
        guild = inter.guild
        if not guild:
            raise UsedNotOnGuild()

        settings = get_economy_settings(guild.id)
        currency = CurrencyType(currency)
        change_balance(
            guild.id,
            member.id,
            amount=amount,
            currency=currency,
        )
        await inter.response.send_message(
            t('balance_changed'),
            ephemeral=True,
        )
        make_history(
            guild.id,
            member.id,
            name='bal_change',
            description=t(
                'balance_changed_history_desc',
                user_id=inter.author.id,
                target_id=member.id,
                amount=f'{amount:+}',
                currency=currency.get_guild_repr(settings)),
        )


def setup(bot) -> None:
    bot.add_cog(EconomyControlCog(bot))
