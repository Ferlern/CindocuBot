import disnake
from disnake.ext import commands

from src.bot import SEBot
from src.database.models import Members
from src.discord_views.embeds import DefaultEmbed
from src.formatters import ordered_list
from src.translation import get_translator

t = get_translator(route='ext.fun')

MEOW_TOP_SIZE = 10

class MeowCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot
    
    @commands.slash_command()
    async def meow(
        self,
        interaction: disnake.GuildCommandInteraction
    ) -> None:
        """
        Команда, показывающая сколько раз ты мяукнул в чате!!!!!!!!!!!😭
        """
        await interaction.response.send_message(
            embed=_create_meow_top_embed(interaction.guild.id)
        )

def _create_meow_top_query(guild_id: int):
    return (
        Members.
        select(Members.user_id, Members.meow_count).
        where((Members.guild_id == guild_id) 
              & (Members.on_guild == True) 
              & (Members.meow_count != 0)).
        order_by(Members.meow_count.desc()). # type: ignore
        limit(MEOW_TOP_SIZE)
    )

def _create_meow_top_embed(guild_id: int) -> disnake.Embed:
    query = _create_meow_top_query(guild_id)
    desc = ordered_list(
        query,
        lambda item: f'<@{item.user_id}> {t("meow_message", count=item.meow_count)}'
    )
    if desc == "": desc = t("meow_lack")
    embed = DefaultEmbed(
        title=t('top_meow'),
        description=desc,
    )
    embed.set_image(
        url="https://i.pinimg.com/originals/d9/b2/9f/d9b29fdd541404f5df42c52362dca5bf.gif"
    )
    return embed

def setup(bot) -> None:
    bot.add_cog(MeowCog(bot))