import asyncio
import disnake
from disnake.ext import commands

from src.converters import interacted_member
from src.bot import SEBot
from src.ext.economy.services import change_balance
from src.discord_views.shortcuts import request_data_via_modal, ModalInput


VALENTINE_PRICE = 100
FEB_CHANNEL = 882377885720121424


class FebCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot

    @commands.slash_command()
    async def valentine(
        self,
        inter: disnake.GuildCommandInteraction,
        member: disnake.Member = commands.Param(converter=interacted_member),
        hide: str = commands.Param(default='false', choices={'Да': 'true', 'Нет': 'false'})
    ) -> None:
        """
        Отправить валентинку

        Parameters
        ----------
        member: Участник, которому вы хотите отправить валентинку
        hide: Не показывать вас как автора валентинки
        """
        channel = inter.guild.get_channel(FEB_CHANNEL)
        if not isinstance(channel, disnake.TextChannel):
            await inter.response.send_message('Не получилось отправить')
            return
        fields = (ModalInput(label='текст', max_length=1024, style=disnake.TextInputStyle.long),)
        try:
            modal_inter, text = await request_data_via_modal(inter, 'Текст валентинки', fields)
        except asyncio.TimeoutError:
            return

        title = ':two_hearts: Валентинка'
        if hide == 'false':
            title += f' от {inter.author.name}'
        embed = disnake.Embed(
            title=title,
            description=text,
            color=disnake.Color.red(),
        )
        change_balance(inter.guild_id, inter.author.id, -VALENTINE_PRICE)
        asyncio.gather(
            channel.send(content=member.mention, embed=embed),
            modal_inter.response.send_message('Валентинка отправлена', ephemeral=True),
        )


def setup(bot) -> None:
    bot.add_cog(FebCog(bot))
