import disnake
from disnake.ext import commands
from typing import Union, Optional

from src.bot import SEBot
from src.logger import get_logger
from src.translation import get_translator
from src.discord_views.embeds import DefaultEmbed
from src.discord_views.paginate.peewee_paginator import PeeweePaginator
from src.database.models import Pets
from src.converters import not_bot_member
from src.utils.experience import format_pet_exp_and_lvl
from src.ext.pets.services import (
    change_main_pet,
    delete_pet,
    get_main_pet,
    rename_pet,
    get_pet_by_id,
    feed_pet,
    restore_energy,
    pet_pet,
    send_to_auction,
)
from src.ext.pets.utils import (
    delete_pet_confirmation,
    rename_pet_request,
    auc_pet_price_request
)


logger = get_logger()
t = get_translator(route='ext.pets')

RESTORE_ENERGY_PRICE = 100
PET_PET_AWARD = 10
# AUCTION_FEE = 15

class PetProfileCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot

    @commands.slash_command()
    async def pets(
        self,
        interaction: disnake.GuildCommandInteraction,
        member=commands.Param(converter=not_bot_member, default=None)
    ) -> None:
        """
        Просмотр информации о питомцах
        """
        is_owner = False
        guild = interaction.guild
        if not member:
            member = interaction.author
            is_owner = True
        pet_paginator = PetPaginator(self.bot, guild, member, is_owner)
        await pet_paginator.start_from(interaction)


class PetPaginator(PeeweePaginator[Pets]):
    def __init__(
        self,
        bot: SEBot,
        guild: disnake.Guild,
        user: disnake.Member,
        is_owner: bool
    ) -> None:
        self.guild = guild
        self.user = user
        self._bot = bot
        self.is_owner = is_owner
        super().__init__(
            Pets,
            items_per_page=5,
            filters={
                'guild': Pets.guild == self.guild.id,
                'user': Pets.user == self.user.id
            }, # type: ignore
            order_by=Pets.id.asc() # type: ignore
        )
        self.current_pet: Optional[Pets] = (
            self.items[0] if self.items else None)
        profile_select_btn = ProfileSelect()
        make_main_btn = MakeMainButton()
        delete_pet_btn = DeletePetButton()
        rename_pet_btn = RenamePetButton()
        feed_pet_btn = FeedPetButton()
        restore_energy_btn = RestoreEnergyButton()
        pet_pet_btn = PetPetButton()
        send_to_auction_btn = SendToAuctionButton()


        if self.is_owner:
            self.add_item(make_main_btn)
            self.add_item(rename_pet_btn)
            self.add_item(delete_pet_btn)   
            self.add_item(send_to_auction_btn)

        self.add_item(profile_select_btn)
        self.add_item(feed_pet_btn)
        self.add_item(restore_energy_btn)
        # self.add_item(pet_pet_btn)


        self._updateable_components = [
            profile_select_btn, make_main_btn,
            delete_pet_btn, rename_pet_btn,
            feed_pet_btn, restore_energy_btn,
            pet_pet_btn, send_to_auction_btn
        ]
        self._update_components()

    async def page_callback(
        self,
        interaction: Union[
            disnake.ModalInteraction,
            disnake.MessageInteraction
        ],
    ) -> None:
        self.current_pet = self.items[0]
        self._update_components()

        await interaction.response.defer()
        await interaction.edit_original_message(
            embed=self.create_embed(),
            view=self
        )

    async def _response(
        self,
        inter: disnake.ApplicationCommandInteraction
    ) -> None:
        self._update_components()

        await inter.response.defer()
        await inter.followup.send(
            embed=self.create_embed(),
            view=self
        )
    
    def create_embed(self) -> disnake.Embed:
        pet = self.current_pet
        if not pet:
            return DefaultEmbed(
                title = t("no_pets")
            )
        
        embed = DefaultEmbed(
            title = t("title", name=pet.name),
        )
        embed.add_field(
            name = t("rarity"),
            value = f"```diff\n{t(self._get_pet_rarity(pet.exp_scale))}```",
            inline = False
        )
        embed.add_field(
            name = t("spec"),
            value = f"```py\n{t(pet.spec)}```", # type: ignore
            inline = False
        ) 
        embed.add_field(t("level"), format_pet_exp_and_lvl(pet.experience, pet.level))
        embed.add_field(t("energy"), f"**{pet.energy}** / **{pet.max_energy}**")
        embed.add_field(t("wins_and_loses"), f"**{pet.wins}** / **{pet.loses}**")
        embed.add_field(
            name = t("stats"),
            value = self._get_pet_stats(pet),
            inline = False
        )
        embed.set_thumbnail(self.user.avatar)

        main_pet = get_main_pet(self.guild.id, self.user.id)
        if main_pet and main_pet.id == pet.id and self.is_owner:
            embed.set_footer(text=t("main_pet"))

        if pet.on_auction:
            embed.set_footer(text=t("on_auction"))

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
            pet_id = self.current_pet.id # type: ignore
            self.update()
            self.current_pet = (
                (self.items[0] if self.items else None)
                if with_deletion
                else get_pet_by_id(pet_id)
            )
        self._update_components()
        await inter.response.edit_message(
            embed=self.create_embed(),
            view=self
        )

    # async def _switch_to_owner_btns(self) -> None:
    #     self.clear_items()


class ProfileSelect(disnake.ui.Select):
    view: PetPaginator

    def __init__(self) -> None:
        super().__init__(
            placeholder=t("choose_pet"),
            row=3
        )

    def update(self) -> None:
        if not self.view.items:
            self.placeholder = t("no_pets_ph")
            self.disabled = True
            self.options = [disnake.SelectOption(label="...")]
            return
        
        options = [
            disnake.SelectOption(
                label=f"{str(item.id)}. {item.name}",
                value=str(index)
            ) for index, item in enumerate(self.view.items, 0)
        ]
        self.options = options

    async def callback(
        self,
        interaction: disnake.MessageCommandInteraction
    ) -> None:
        view = self.view
        view.current_pet = view.items[int(self.values[0])]
        await view.update_view(interaction)


class SwitchOwnerButtons(disnake.ui.Button):
    view: PetPaginator

    def __init__(self) -> None:
        super().__init__(
            label="Owner",
            style=disnake.ButtonStyle.blurple
        )
    
    def update(self) -> None:
        view = self.view
        self.disabled = True if (
            not view.is_owner 
            or not view.current_pet
            or view.current_pet.on_auction
        ) else False

    async def callback(
        self,
        interaction: disnake.MessageCommandInteraction
    ) -> None:
        ...


class SwitchGuestsButtons(disnake.ui.Button):
    view: PetPaginator

    def __init__(self) -> None:
        super().__init__(
            label="Guests",
            style=disnake.ButtonStyle.blurple
        )
    
    def update(self) -> None:
        view = self.view
        self.disabled = True if (
            not view.current_pet
        ) else False

    async def callback(
        self,
        interaction: disnake.MessageCommandInteraction
    ) -> None:
        ...


class MakeMainButton(disnake.ui.Button):
    view: PetPaginator

    def __init__(self) -> None:
        super().__init__(
            label = t("make_main_button"),
            style = disnake.ButtonStyle.green,
            row=1
        )

    def update(self) -> None:
        if self.view:
            pet = self.view.current_pet
            self.disabled = True if (
                not pet
                or pet.on_auction
            ) else False

    async def callback(
        self,
        interaction: disnake.MessageCommandInteraction
    ) -> None:
        pet = self.view.current_pet
        if not pet: return

        change_main_pet(
            interaction.guild.id, # type: ignore
            interaction.user.id,
            pet
        )
        await self.view.update_view(interaction)


class DeletePetButton(disnake.ui.Button):
    view: PetPaginator

    def __init__(self) -> None:
        super().__init__(
            label = t("delete_pet_button"),
            style = disnake.ButtonStyle.red,
            row=1
        )
        
    def update(self) -> None:
        if self.view:
            pet = self.view.current_pet
            self.disabled = True if (
                not pet
                or pet.on_auction
            ) else False

    async def callback(
        self,
        interaction: disnake.MessageCommandInteraction
    ) -> None:
        pet = self.view.current_pet
        if not pet: return

        confirmation = await delete_pet_confirmation(interaction)
        if confirmation == t("delete_placeholder"):
            delete_pet(pet.id)
            await self.view.update_view(
                interaction, with_rebuild=True, with_deletion=True
            )
            # await interaction.followup.send(t("delete_success"), ephemeral=True)
        else:
            await interaction.response.send_message(
                t("delete_not_confirmed"), ephemeral=True
            )


class RenamePetButton(disnake.ui.Button):
    view: PetPaginator

    def __init__(self) -> None:
        super().__init__(
            label = t("rename_pet_button"),
            style = disnake.ButtonStyle.gray,
            row=1
        )

    def update(self) -> None:
        if self.view:
            pet = self.view.current_pet
            self.disabled = True if (
                not pet
                or pet.on_auction
            ) else False

    async def callback(
        self,
        interaction: disnake.MessageCommandInteraction
    ) -> None:
        pet = self.view.current_pet
        if not pet: return

        new_name = await rename_pet_request(interaction)
        if not new_name:
            return
        
        rename_pet(pet.id, new_name)
        await self.view.update_view(interaction, with_rebuild=True)


class FeedPetButton(disnake.ui.Button):
    view: PetPaginator

    def __init__(self) -> None:
        super().__init__(
            label=t("feed_pet_button"),
            style=disnake.ButtonStyle.green,
            row=2
        )

    def update(self) -> None:
        if self.view:
            pet = self.view.current_pet
            self.disabled = True if (
                not pet
            ) else False

    async def callback(
        self,
        inter: disnake.MessageCommandInteraction
    ) -> None:
        pet = self.view.current_pet
        if not pet: return
        feed_pet(
            pet.id, inter.guild.id, inter.user.id # type: ignore
        )
        await self.view.update_view(inter, with_rebuild=True)


class RestoreEnergyButton(disnake.ui.Button):
    view: PetPaginator

    def __init__(self) -> None:
        super().__init__(
            label=t("restore_energy_button"),
            style=disnake.ButtonStyle.blurple,
            row=2
        )

    def update(self) -> None:
        if self.view:
            pet = self.view.current_pet
            self.disabled = True if (
                not pet
            ) else False

    async def callback(
        self,
        inter: disnake.MessageCommandInteraction
    ) -> None:
        pet = self.view.current_pet
        if not pet: return
        restore_energy(
            pet.id, inter.guild.id, # type: ignore
            inter.user.id, amount=100
        )
        await self.view.update_view(inter, with_rebuild=True)


class PetPetButton(disnake.ui.Button):
    view: PetPaginator

    def __init__(self) -> None:
        super().__init__(
            label=t("pet_pet_button"),
            style=disnake.ButtonStyle.gray,
            row=2
        )

    def update(self) -> None:
        if self.view:
            pet = self.view.current_pet
            self.disabled = True if (
                not pet
            ) else False

    async def callback(
        self,
        inter: disnake.MessageCommandInteraction
    ) -> None:
        pet = self.view.current_pet
        if not pet: return

        if pet.petted or (pet.user.id != inter.user.id): # type: ignore
            await inter.response.send_message(t("petted"), ephemeral=True)
            return
    
        pet_pet(pet.id, inter.guild.id, inter.user.id, PET_PET_AWARD) # type: ignore
        await self.view.update_view(inter, with_rebuild=True)
        await inter.followup.send(t("petted_with_money"), ephemeral=True)


class SendToAuctionButton(disnake.ui.Button):
    view: PetPaginator

    def __init__(self) -> None:
        super().__init__(
            label=t("send_to_auction_button"),
            style=disnake.ButtonStyle.gray,
            row=4
        )

    def update(self) -> None:
        if self.view:
            pet = self.view.current_pet
            self.disabled = True if (
                not pet
                or pet.on_auction
            ) else False

    async def callback(
        self,
        inter: disnake.MessageCommandInteraction
    ) -> None:
        guild_id = inter.guild_id
        user_id = inter.user.id
        view = self.view

        modal_data = await auc_pet_price_request(inter)        
        price = self._data_to_price(modal_data)

        if not price:
            await inter.followup.send(t("not_a_number"), ephemeral=True)
            return

        send_to_auction(guild_id, user_id, view.current_pet.id, price) # type: ignore
        logger.info('user %d setted item for auction', user_id)
        await view.update_view(inter, with_rebuild=True)
        await inter.followup.send(t("auc_item_set"), ephemeral=True)

    def _data_to_price(self, modal_data: Optional[str]) -> Optional[int]:
        if not modal_data or not modal_data.strip():
            return None
        
        try: return abs(int(modal_data))
        except ValueError: return None


def setup(bot: SEBot) -> None:
    bot.add_cog(PetProfileCog(bot))