import aiohttp
import disnake
from disnake.ext import commands

from src.discord_views.embeds import DefaultEmbed
from src.converters import interacted_member
from src.bot import SEBot
from src.ext.fun.actions import Categories


class FunCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot

    @commands.slash_command()
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def action(
        self,
        inter: disnake.GuildCommandInteraction,
        member=commands.Param(converter=interacted_member),
        action=commands.Param(
            choices={entry.get_translated_name(): entry.name for entry in Categories}
        ),
    ) -> None:
        """
        Выполнить дейстие

        Parameters
        ----------
        member: Участник, с которым вы хотите сделать действие
        action: Действие, которое вы хотите сделать
        """
        await self._send_gif(inter, member, Categories[action])

    async def _send_gif(
        self,
        inter: disnake.GuildCommandInteraction,
        target: disnake.Member,
        category: Categories,
    ) -> None:
        embed = DefaultEmbed(
            description=category.get_embed_text(inter.author, target)  # type: ignore
        )
        embed.set_image(url=await get_random_url(category))
        await inter.response.send_message(target.mention, embed=embed)


async def get_random_url(category: Categories) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.waifu.pics/sfw/{category}') as response:
            json_resp = await response.json()
            return json_resp['url']


def setup(bot) -> None:
    bot.add_cog(FunCog(bot))
