import disnake
from disnake.ext import commands
import random

from src.logger import get_logger
from src.translation import get_translator
from src.bot import SEBot
from src.discord_views.embeds import DefaultEmbed
from src.discord_views.base_view import BaseView
from src.database.models import psql_db, FontainCounter
from src.ext.economy.services import change_balance


logger = get_logger()
t = get_translator(route='ext.fun')


AMOUNT_OF_DONATION = 100
MIN_FOUNTAIN_NEEDED = 500
MAX_FOUNTAIN_NEEDED = 10000
FOUNTAIN_THUMBNAIL = "https://media1.tenor.com/m/G1oHcSvW6voAAAAC/anime-gif-anime.gif"
WINNER_MES_DELETE_AFTER = 60


class FountainCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot

    @commands.slash_command()
    async def fountain(
        self,
        inter: disnake.GuildCommandInteraction
    ) -> None:
        """
        Брось монетку в фонтан и, кто знает, может тебе сегодня повезет?
        """
        if not isinstance(inter.channel, disnake.TextChannel):
            await inter.response.send_message(
                t('only_for_text_channels'),
                ephemeral=True
            )
            return

        view = FountainView(self.bot, inter.guild)
        await view.start_from(inter)


class FountainView(BaseView):
    def __init__(
        self,
        bot: SEBot,
        guild: disnake.Guild
    ) -> None:
        self.bot = bot
        self.guild = guild
        super().__init__(timeout=300)

        self.add_item(DonateMoney())

    def create_embed(self) -> disnake.Embed:
        amount = get_fountain_counter(
            self.guild.id
        ).money_count

        embed = DefaultEmbed(
            title = t("fountain_title"),
            description = t("fountain_desc",
                             amount=amount)
        )
        embed.set_thumbnail(FOUNTAIN_THUMBNAIL)
        return embed
    
    async def interaction_check(
        self,
        interaction: disnake.MessageInteraction
    ) -> bool:
        return True

    async def _response(
        self,
        inter: disnake.ApplicationCommandInteraction
    ) -> None:
        await inter.response.send_message(
            embed=self.create_embed(),
            view=self
        )

    async def update_view(
        self,
        inter: disnake.MessageCommandInteraction
    ) -> None:
        await inter.response.edit_message(
            embed=self.create_embed(),
            view=self
        )


class DonateMoney(disnake.ui.Button):
    view: FountainView

    def __init__(self) -> None:
        super().__init__(
            label=t("donate_money_button",
                     amount=AMOUNT_OF_DONATION),
            style=disnake.ButtonStyle.green
        )

    async def callback(
        self,
        inter: disnake.MessageCommandInteraction
    ) -> None:
        def is_winner_callback(
            is_winner: bool = False,
            amount: int = 0
        ) -> None:
            if is_winner:
                self.view.bot.loop.create_task(
                    self._send_winner_message(
                        inter.channel, # type: ignore
                        inter.user.id,
                        amount
                    )
                )

        add_money_to_fountain(
            self.view.guild.id,
            inter.user.id,
            AMOUNT_OF_DONATION,
            is_winner_callback
        )
        await self.view.update_view(inter)

    async def _send_winner_message(
        self, 
        channel: disnake.TextChannel,
        user_id: int, amount: int,
    ) -> None:
        embed = DefaultEmbed(
            title = t('fountain_winner'),
            description = t('fountain_winner_desc',
                user_id=user_id, amount=amount
            )
        )
        await channel.send(
            embed=embed,
            delete_after=WINNER_MES_DELETE_AFTER
        )

@psql_db.atomic()
def get_fountain_counter(
    guild_id: int,
    /
) -> FontainCounter:
    counter, created = FontainCounter.get_or_create(
        guild = guild_id
    )
    if created:
        counter.money_needed = random.randint(
            MIN_FOUNTAIN_NEEDED, MAX_FOUNTAIN_NEEDED
        )
        counter.save()
    return counter


@psql_db.atomic()
def add_money_to_fountain(
    guild_id: int,
    user_id: int,
    amount: int,
    callback
) -> None:
    change_balance(guild_id, user_id, -amount)
    check_for_award(guild_id, user_id, amount, callback)


@psql_db.atomic()
def check_for_award(
    guild_id: int,
    user_id: int,
    amount: int,
    callback
) -> None:
    counter = get_fountain_counter(guild_id)
    counter.money_count += amount
    m_c = counter.money_count
    m_n = counter.money_needed
    if m_c >= m_n:
        change_balance(guild_id, user_id, m_c)
        counter.money_count = 0
        counter.money_needed = random.randint(
            MIN_FOUNTAIN_NEEDED, MAX_FOUNTAIN_NEEDED
        )
        callback(is_winner=True, amount=m_c)  
    counter.save()
    

def setup(bot: SEBot) -> None:
    bot.add_cog(FountainCog(bot))