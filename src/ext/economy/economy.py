import time

import disnake
from disnake.ext import commands

from src.bot import SEBot
from src.translation import get_translator
from src.discord_views.embeds import DefaultEmbed
from src.converters import interacted_member
from src.formatters import from_user_to_user
from src.custom_errors import DailyAlreadyReceived
from src.utils.slash_shortcuts import only_guild
from src.ext.economy.services import (change_balance, get_economy_settings,
                                      take_bonus)
from src.ext.economy.shops.shops import get_not_empty_shops, Shop
from src.discord_views.switch import ViewSwitcher
from src.utils.time_ import second_until_end_of_day


t = get_translator(route="ext.economy")


class EconomyCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    @commands.slash_command(**only_guild)
    async def daily(self,
                    inter: disnake.ApplicationCommandInteraction
                    ) -> None:
        """
        Получить ежедневную награду
        """
        economy_settings = get_economy_settings(inter.guild.id)  # type: ignore
        guild_id = inter.guild.id  # type: ignore
        daily = economy_settings.daily
        coin = economy_settings.coin
        timestamp = disnake.utils.format_dt(
            time.time() + second_until_end_of_day(), 'R'
        )
        embed = DefaultEmbed()

        try:
            balance = take_bonus(
                guild_id,
                inter.author.id, daily  # type: ignore
            ).balance
            embed = DefaultEmbed(
                title=t('daily_recieved'),
                description=t('daily_recieved_desc',
                              timestamp=timestamp,
                              balance=balance,
                              daily=daily,
                              coin=coin)
            )
        except DailyAlreadyReceived:
            embed = DefaultEmbed(
                title=t('daily_already_recieved'),
                description=t('daily_already_recieved_desc',
                              timestamp=timestamp)
            )
        finally:
            embed.set_thumbnail(url=inter.author.display_avatar.url)
            await inter.response.send_message(embed=embed)

    @commands.slash_command(**only_guild)
    async def shop(self, inter: disnake.ApplicationCommandInteraction):
        """
        Магазины
        """
        shops = get_not_empty_shops(inter.author)  # type: ignore
        if not shops:
            await inter.response.send_message(
                t('all_shops_empty'),
                ephemeral=True,
            )
            return

        switcher = ShopSwitcher()
        for shop in shops:
            switcher.add_view(
                shop,
                label=shop.name,
            )
        await switcher.start_from(inter)

    @commands.slash_command(**only_guild)
    async def transfer(self,
                       inter: disnake.ApplicationCommandInteraction,
                       member=commands.Param(converter=interacted_member),
                       amount: commands.Range[1, ...] = commands.Param(),
                       ) -> None:
        """
        Перевести валюту сервера другому участнику

        Parameters
        ----------
        member: Участник, которому будет переведена валюта
        amount: Количество валюты для перевода
        """
        guild_id: int = inter.guild.id  # type: ignore
        coin = get_economy_settings(guild_id).coin
        change_balance(guild_id, inter.author.id, -amount)  # noqa
        change_balance(guild_id, member.id, amount)

        embed = DefaultEmbed(
            title=t('transfered'),
            description=f'{from_user_to_user(inter.author, member)} '
                        f'{amount} {coin}'
        )
        await inter.response.send_message(embed=embed)


class ShopSwitcher(ViewSwitcher[Shop]):
    def __init__(self) -> None:
        super().__init__(placeholder=t('shop_select'))

    async def _resolve_selection(
        self,
        view: Shop,
        inter: disnake.MessageInteraction,
    ) -> None:
        await inter.response.edit_message(
            embed=view.create_embed(),
            view=view,
        )


def setup(bot):
    bot.add_cog(EconomyCog(bot))
