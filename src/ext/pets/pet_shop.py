import disnake

from src.ext.economy.shops.base import Shop
from src.database.models import EconomySettings
from src.translation import get_translator
from src.ext.pets.services import buy_feed_stuff, get_feed_stuff


t = get_translator(route="ext.pets")


class PetShop(Shop):
    def __init__(
        self,
        author: disnake.Member,
        settings: EconomySettings
    ) -> None:
        self._settings = settings
        super().__init__(author, settings, timeout=300)
        self.add_item(BuyFeedStuffSelect(self._settings))

    def create_embed(self) -> disnake.Embed:
        return disnake.Embed(
            title = t('pet_shop'),
            description=self._create_desc()
        )
    
    def _create_desc(self) -> str:
        settings = self._settings
        desc = t(
            "shop_desc",
            price = settings.feed_stuff_price,
            coin = settings.coin,
        )
        current: int = get_feed_stuff(
            settings.guild_id.id, self.author.id)
        desc += t("shop_desc_add", count=current)
        return desc

    def is_empty(self) -> bool:
        return False
    
    @property
    def name(self) -> str:
        return t("pet_shop_select")
    
    async def _response(
        self,
        inter: disnake.ApplicationCommandInteraction
    ) -> None:
        await inter.response.send_message(
            embed=self.create_embed(),
            view=self,
        )

    async def update(
        self,
        interaction: disnake.MessageInteraction
    ) -> None:
        await interaction.response.edit_message(
            embed=self.create_embed(),
            view=self
        )

class BuyFeedStuffSelect(disnake.ui.Select):
    view: PetShop

    def __init__(self, settings: EconomySettings) -> None:
        self._settings = settings
        options = [
            disnake.SelectOption(
                label=t("feed_stuff")
            )
        ]
        super().__init__(options=options)

    async def callback(
        self,
        inter: disnake.MessageInteraction
    ) -> None:
        buy_feed_stuff(
            inter.guild.id, # type: ignore
            inter.user.id,
            self._settings.feed_stuff_price
        )
        await self.view.update(inter)
        await inter.followup.send(t("buy_success"), ephemeral=True)

