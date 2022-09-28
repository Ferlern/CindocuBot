from enum import Enum

import aiohttp
import disnake
from disnake.ext import commands

from src.discord_views.embeds import DefaultEmbed
from src.translation import get_translator
from src.converters import interacted_member
from src.bot import SEBot


t = get_translator(route='ext.fun')


class Categories(str, Enum):
    PAT = 'pat'
    KISS = 'kiss'
    HUG = 'hug'


class FunCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    @commands.slash_command()
    async def hug(
        self,
        inter: disnake.GuildCommandInteraction,
        member=commands.Param(converter=interacted_member),
    ) -> None:
        await self._send_gif(inter, member, Categories.HUG)

    @commands.slash_command()
    async def kiss(
        self,
        inter: disnake.GuildCommandInteraction,
        member=commands.Param(converter=interacted_member),
    ) -> None:
        await self._send_gif(inter, member, Categories.KISS)

    @commands.slash_command()
    async def pat(
        self,
        inter: disnake.GuildCommandInteraction,
        member=commands.Param(converter=interacted_member),
    ) -> None:
        await self._send_gif(inter, member, Categories.PAT)

    async def _send_gif(
        self,
        inter: disnake.GuildCommandInteraction,
        target: disnake.Member,
        category: Categories,
    ):
        embed = DefaultEmbed(
            description=t(
                category,
                user_id=inter.author.id,
                target_id=target.id
            )
        )
        embed.set_image(url=await get_random_url(category))
        await inter.response.send_message(embed=embed)


async def get_random_url(category: Categories) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.waifu.pics/sfw/{category}') as response:
            json_resp = await response.json()
            return json_resp['url']


def setup(bot):
    bot.add_cog(FunCog(bot))
