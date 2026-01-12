import disnake
from typing import Optional, Union

from src.bot import SEBot
from src.translation import get_translator
from src.discord_views.paginate.peewee_paginator import PeeweePaginator
from src.database.models import AuctionPet, Pets
from src.discord_views.embeds import DefaultEmbed
from src.utils.experience import format_pet_exp_and_lvl
from src.ext.pets.services import get_pet_auction_item, buy_auc_item
from src.utils import custom_events


t = get_translator(route='ext.pets')


class AuctionItemsView(PeeweePaginator[AuctionPet]):
    def __init__(
        self,
        bot: SEBot,
        guild: disnake.Guild,
        user: disnake.User | disnake.Member
    ) -> None:
        self.bot = bot
        self.guild = guild
        self.user = user
        super().__init__(
            AuctionPet,
            items_per_page=10,
            filters={
                'guild': AuctionPet.guild == self.guild.id,
                'user': AuctionPet.owner != self.user.id
            }, # type: ignore
            order_by=AuctionPet.pet.asc() # type: ignore
        )
        self.auction_item: Optional[AuctionPet] = (
            self.items[0] if self.items else None)
        item_select = AuctionItemSelect()
        buy_btn = BuyItemButton()

        self.add_item(item_select)
        self.add_item(buy_btn)

        self._updateable_components = [item_select, buy_btn]
        self._update_components()

    async def page_callback(
        self,
        interaction: Union[
            disnake.ModalInteraction,
            disnake.MessageInteraction
        ],
    ) -> None:
        self._update_components()

        await interaction.response.defer()
        await interaction.edit_original_message(
            embed=await self.create_embed(),
            view=self
        )

    async def _response(
        self,
        inter: disnake.ApplicationCommandInteraction
    ) -> None:
        self._update_components()

        await inter.response.defer()
        await inter.followup.send(
            embed=await self.create_embed(),
            view=self
        )
    
    async def create_embed(self) -> disnake.Embed:
        item = self.auction_item
        if not item:
            return DefaultEmbed(
                title = t("no_auc_items")
            )
        
        pet = item.pet
        embed = DefaultEmbed(
            title = t("auc_title", name=pet.name),
        )
        embed.add_field(
            name = t("rarity"),
            value = f"```diff\n{t(self._get_pet_rarity(pet.exp_scale))}```",
            inline = False
        )
        embed.add_field(
            name = t("spec"),
            value = f"```py\n{t(pet.spec)}```",
            inline = False
        ) 
        embed.add_field(t("level"), format_pet_exp_and_lvl(pet.experience, pet.level))
        embed.add_field(t("wins_and_loses"), f"**{pet.wins}** / **{pet.loses}**")
        embed.add_field(
            name = t("stats"),
            value = self._get_pet_stats(pet),
            inline = False
        )

        owner = await self.bot.getch_user(item.owner.id)
        sell_value = t(
            "sell_value",
            owner=owner.mention if owner else "???",
            price=item.price,
            timestamp = disnake.utils.format_dt(
                item.sale_date, 'f'
            )
        ) 
        embed.add_field(
            name = t("sell_info"),
            value = sell_value,
            inline = False
        )
        if owner:
            embed.set_thumbnail(owner.avatar)
        return embed
    
    def _update_components(self) -> None:
        for component in self._updateable_components:
            component.update()

    def _get_pet_rarity(self, exp_scale: float) -> str:
        return {
            1.0: "default",
            2.0: "legendary"
        }[exp_scale]
    
    def _get_pet_stats(self, pet: Pets) -> str:
        stats = (
            "```\n" +
            t("health", max_health=pet.max_health, health=pet.health) +
            t("strength", strength=pet.strength) +
            t("dexterity", dexterity=pet.dexterity) +
            t("intellect", intellect=pet.intellect) +
            "```"
        )
        return stats
    
    async def update_view(
        self,
        inter: disnake.MessageCommandInteraction,
        with_rebuild = False,
        with_deletion = False,
    ) -> None:
        if with_rebuild:
            item: AuctionPet = self.auction_item # type: ignore
            self.update()
            self.auction_item = (
                (self.items[0] if self.items else None)
                if with_deletion
                else get_pet_auction_item(
                    item.guild.id,
                    item.owner.id,
                    item.pet.id
                )
            )
        self._update_components()
        await inter.response.edit_message(
            embed=await self.create_embed(),
            view=self
        )


class AuctionItemSelect(disnake.ui.Select):
    view: AuctionItemsView

    def __init__(self) -> None:
        super().__init__(
            placeholder=t("choose_item"),
            row=2
        )

    def update(self) -> None:
        if not self.view.items:
            self.placeholder = t("no_items_ph")
            self.disabled = True
            self.options = [disnake.SelectOption(label="...")]
            return
        
        options = [
            disnake.SelectOption(
                label=f"{item.pet.name}, {item.pet.level} lvl | {item.price}",
                value=str(index)
            ) for index, item in enumerate(self.view.items, 0)
        ]
        self.options = options

    async def callback(
        self,
        interaction: disnake.MessageCommandInteraction
    ) -> None:
        view = self.view
        view.auction_item = view.items[int(self.values[0])]
        await view.update_view(interaction)


class BuyItemButton(disnake.ui.Button):
    view: AuctionItemsView

    def __init__(self) -> None:
        super().__init__(
            label=t("buy_item_button"),
            style=disnake.ButtonStyle.green,
            row=1
        )

    def update(self) -> None:
        self.disabled = True if (
            not self.view.auction_item
        ) else False

    async def callback(
        self,
        inter: disnake.MessageCommandInteraction
    ) -> None:
        item = self.view.auction_item
        if not item:
            return

        proceed = buy_auc_item(
            inter.guild.id, # type: ignore
            inter.user.id,
            item.owner.id,
            item.pet,
            item.price
        )

        self.view.bot.dispatch(
            custom_events.EventName.AUCTION_ITEM_SOLD,
            guild_id=item.guild.id,
            owner_id=item.owner.id,
            buyer_id=inter.user.id,
            proceed=proceed
        )

        await self.view.update_view(inter, with_rebuild=True, with_deletion=True)
        await inter.followup.send(t("item_buy_success"), ephemeral=True)