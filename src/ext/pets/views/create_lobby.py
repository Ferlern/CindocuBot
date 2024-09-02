import disnake

from src.bot import SEBot
from src.logger import get_logger
from src.translation import get_translator
from src.discord_views.base_view import BaseView
from src.discord_views.embeds import DefaultEmbed
from src.ext.pets.classes import PetsGame, Lobby
from src.ext.game.utils import user_to_player
from src.ext.pets.views.lobby import LobbyView


logger = get_logger()
t = get_translator(route='ext.pet_battle')


class CreateLobbyView(BaseView):
    def __init__(
        self,
        bot: SEBot,
        guild: disnake.Guild,
        game_channel: disnake.TextChannel
    ) -> None:
        self.bot = bot
        self.guild = guild
        self.game_channel = game_channel
        super().__init__(timeout=180)

        self.add_item(PVPButton())
        self.add_item(PVEButton())

    def create_embed(self) -> disnake.Embed:
        return DefaultEmbed(title=t("choose_mode"))
    
    async def _response(
        self,
        inter: disnake.ApplicationCommandInteraction
    ) -> None:
        await inter.response.send_message(
            embed=self.create_embed(),
            view=self,
            ephemeral=True
        )


class PVPButton(disnake.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label=t("pvp_mode"),
            style=disnake.ButtonStyle.red
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        accepted = await self._accept_create_lobby(user_to_player(interaction.user), interaction)
        if not accepted:
            await interaction.response.send_message(t("already_created"), ephemeral=True)
            return

        await interaction.response.edit_message()

    async def _accept_create_lobby(self, creator, inter) -> bool:
        view = self.view

        lobby = Lobby(
            guild = view.guild,
            creator = creator,
            game = PetsGame()
        )
        lobby.add(creator)
        if lobby.is_already_creator:
            return False

        view = LobbyView(
            bot = view.bot,
            game_channel = view.game_channel,
            lobby = lobby
        )
        await view.create_lobby(inter)
        return True


class PVEButton(disnake.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label=t("pve_mode"),
            style=disnake.ButtonStyle.green,
            disabled=True
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.edit_message(
            embed=self.view.create_embed(),
            view=self.view
        )