import disnake

from src.discord_views.embeds import DefaultEmbed
from src.translation import get_translator
from src.logger import get_logger
from src.custom_errors import CriticalException
from src.formatters import to_mention
from src.ext.game.services.lobby import Lobby
from src.ext.game.views.game_interfaces import DiscordInterface
from src.ext.game.views.join_button import JoinGameButton
from src.ext.game.views.open_close_button import OpenCloseTableButton
from src.ext.game.views.kick_select import KickPlayerSelect
from src.ext.game.views.start_button import StartGameButton
from src.ext.game.views.invite_select import InviteSelect


logger = get_logger()
t = get_translator(route="ext.games")


class LobbyView(disnake.ui.View):
    def __init__(
        self,
        guild: disnake.Guild,
        lobby: Lobby,
        lobby_name: str,
        interface_type: type[DiscordInterface],
    ) -> None:
        super().__init__(timeout=180)
        self.lobby = lobby
        self.interface_type = interface_type
        self.message = None
        self.guild = guild
        self._lobby_name = lobby_name

        open_close_button = OpenCloseTableButton()
        kick_select = KickPlayerSelect()

        self.add_item(JoinGameButton())
        self.add_item(StartGameButton())
        self.add_item(InviteSelect())
        self.add_item(open_close_button)
        self.add_item(kick_select)

        self._updateable_components = [open_close_button, kick_select]
        self._update_components()

    async def update(self) -> None:
        if not self.message:
            raise CriticalException('GameTable has no message during update')
        self._update_components()
        await self.message.edit(embed=self.create_embed(), view=self)

    async def update_using(self, inter: disnake.MessageInteraction) -> None:
        self._update_components()
        await inter.response.edit_message(embed=self.create_embed(), view=self)

    async def start_from(self, inter: disnake.ApplicationCommandInteraction) -> None:
        await inter.response.send_message(embed=self.create_embed(), view=self)
        self.message = await inter.original_message()

    def create_embed(self) -> disnake.Embed:
        return DefaultEmbed(
            title=t('table'),
            description=t(
                'table_desc',
                game_name=self._lobby_name,
                host_id=self.lobby.creator.player_id,
                players=', '.join([to_mention(player.player_id) for player in self.lobby.players]),
                bet=self.lobby.bet,
                current=len(self.lobby),
                limit=self.lobby.game.max_players,
            ),
        )

    async def on_timeout(self) -> None:
        await self.message.edit(view=None, embed=DefaultEmbed(  # type: ignore
            title=t('table'),
            description=t('timeout'),
        ))
        self.lobby.clear()

    def _update_components(self) -> None:
        for component in self._updateable_components:
            component.update()
