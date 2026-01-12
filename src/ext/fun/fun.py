import aiohttp
import disnake
from disnake.ext import commands

from src.ext.members.services import get_member
from src.discord_views.embeds import DefaultEmbed
from src.converters import interacted_member
from src.bot import SEBot
from src.custom_errors import ActionRestricted
from src.ext.fun.categories import Categories
from src.ext.actions.actions import is_action_restricted


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
        Выполнить действие

        Parameters
        ----------
        member: Участник, с которым вы хотите сделать действие
        action: Действие, которое вы хотите сделать
        """
        member_data = get_member(inter.guild.id, member.id)
        action = Categories[action]
        if isinstance(inter.author, disnake.Member):
            if is_action_restricted(action.value, inter.author, member_data.restrictions):
                raise ActionRestricted
            await self._send_gif(inter, member, action)

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
        async with session.get(f'https://api.waifu.pics/sfw/{category.value}') as response:
            json_resp = await response.json()
            return json_resp['url']


def setup(bot) -> None:
    bot.add_cog(FunCog(bot))
