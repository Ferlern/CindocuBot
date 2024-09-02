import disnake
from typing import Optional

from src.bot import SEBot
from src.logger import get_logger
from src.translation import get_translator
from src.discord_views.embeds import DefaultEmbed
from src.ext.pets.services import create_game_channel_message
from src.ext.pets.views.create_lobby import CreateLobbyView
from src.ext.pets.services import get_main_pet, accept_consume_energy


logger = get_logger()
t = get_translator(route='ext.pet_battle')

LOBBY_IMAGE = "https://i.imgur.com/tUy6omm.png"


class PetBattleView(disnake.ui.View):
    def __init__(
        self,
        bot: SEBot,
        guild: disnake.Guild,
        game_channel: disnake.TextChannel,
        game_message: Optional[disnake.Message]
    ) -> None:
        self.bot = bot
        self.guild = guild
        self.game_channel = game_channel
        self.game_message = game_message
        super().__init__(timeout=None)

        self.add_item(OpenLobbyButton())
        self.add_item(RulesButton())

    async def create_or_update_game_message(self) -> None:
        if self.game_message:
            logger.debug(
                'game message already on channel: %s in guild %s',
                self.game_channel.name,
                self.guild.name
            )
            await self.game_message.edit(view=self)
            return
        
        logger.debug(
            'sending interactive game message on channel: %s in guild %s',
            self.game_channel.name,
            self.guild.name
        )
        game_message = await self.game_channel.send(
            embed = self.create_embed(),
            view = self
        )
        create_game_channel_message(self.guild.id, game_message.id)

    def create_embed(self) -> disnake.Embed:
        embed = DefaultEmbed(
            title=t("pet_battle_title"),
            description = t("pet_battle_desc")
        )
        embed.set_image(LOBBY_IMAGE)
        return embed


class OpenLobbyButton(disnake.ui.Button):
    view: PetBattleView

    def __init__(self) -> None:
        super().__init__(
            label=t("start_btn"),
            style=disnake.ButtonStyle.green
        )

    async def callback(
        self,
        interaction: disnake.ApplicationCommandInteraction
    ) -> None:
        if not (pet := get_main_pet(
            interaction.guild.id, interaction.user.id)): # type: ignore
            await interaction.response.send_message(
                t("no_main_pet_err"),
                ephemeral=True
            )
            return
        
        if pet.spec == 'demon':
            await interaction.response.send_message(
                t("custom_pet_err"),
                ephemeral=True
            )
            return
        
        if pet.health <= 0:
            await interaction.response.send_message(
                t("zero_health_pet_err"),
                ephemeral=True
            )
            return
        
        consumed = accept_consume_energy(pet.id)
        if not consumed:
            await interaction.response.send_message(
                t("not_enough_energy_err"),
                ephemeral=True
            )
            return
        
        view = self.view
        lobby_view = CreateLobbyView(
            view.bot, view.guild, view.game_channel
        )
        await lobby_view.start_from(interaction)


class RulesButton(disnake.ui.Button):
    view: PetBattleView

    def __init__(self) -> None:
        super().__init__(
            label=t("rules_btn"),
            style=disnake.ButtonStyle.blurple
        )

    def create_embed(self) -> disnake.Embed:
        return DefaultEmbed(
            description=t('rules_desc')
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.send_message(
            embed=self.create_embed(), ephemeral=True)

        
