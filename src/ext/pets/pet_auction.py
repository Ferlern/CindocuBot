from typing import Any
import disnake
from disnake.ext import commands

from src.bot import SEBot
from src.logger import get_logger
from src.translation import get_translator
from src.discord_views.switch import ViewSwitcher
from src.ext.pets.views.auction import *
from src.utils import custom_events
from src.ext.pets.services import create_auc_mail


logger = get_logger()
t = get_translator(route='ext.pets')


class PetAuctionCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    @commands.slash_command()
    async def auction(
        self,
        inter: disnake.GuildCommandInteraction
    ) -> None:
        """
        Аукцион, где можно купить себе питомца.
        """
        bot = self.bot
        guild = inter.guild
        user = inter.user

        switcher = AuctionSwitcher()
        switcher.add_view(AuctionItemsView(bot, guild, user), label=t('items_for_sale'))
        switcher.add_view(OwnerItemsView(bot, guild, user), label=t('your_items'))
        switcher.add_view(MailView(bot, guild, user), label=t('mail_title'))
        await switcher.start_from(inter)
    
    @commands.Cog.listener(f'on_{custom_events.EventName.AUCTION_ITEM_SOLD}')
    async def auc_listener(
        self,
        guild_id: int, owner_id: int,
        buyer_id: int, proceed: int
    ) -> None:
        logger.info("%d's item was bought by %d", owner_id, buyer_id)
        create_auc_mail(guild_id, owner_id, buyer_id, proceed)

class AuctionSwitcher(ViewSwitcher):
    async def _resolve_selection(
        self, view, inter: disnake.MessageInteraction,
    ) -> None:
        await inter.response.edit_message(
            embed=view.create_embed(),  # type: ignore
            view=view,
            allowed_mentions=disnake.AllowedMentions(users=False),
        )

    
def setup(bot: SEBot) -> None:
    bot.add_cog(PetAuctionCog(bot))