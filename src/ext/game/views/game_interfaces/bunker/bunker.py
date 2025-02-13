import disnake

from src.bot import SEBot
from src.logger import get_logger
from src.translation import get_translator
from src.ext.game.services.games import BunkerGame
from src.ext.game.utils import player_to_member
from src.ext.game.views.game_interfaces import ChannelGameInterface
from .master_panel import MasterPanelInterface
from src.ext.game.views.bunker_views import CardsSelect, ShowPlayerCardButton, MasterPanelButton

logger = get_logger()
t = get_translator(route='ext.games')

class BunkerDiscordInterface(ChannelGameInterface[BunkerGame]):
    def __init__(  # pylint: disable=too-many-arguments
        self,
        bot: SEBot,
        guild: disnake.Guild,
        message: disnake.Message,
        game: BunkerGame,
        *,
        timeout = 9000,
    ) -> None:
        super().__init__(bot, guild, message, game, timeout=timeout)
        self.create_cards_map()
        self.master_panel_view = MasterPanelInterface(bot, guild, message, game, self)
        self.current_card = list(self.cards_map)[0]

        card_select = CardsSelect()
        self.add_item(card_select)
        self.add_item(ShowPlayerCardButton())
        self.add_item(MasterPanelButton())

        self._updateable_components = [card_select]
        self._update_components()

    def create_embed(self) -> disnake.Embed:
        card = self.cards_map.get(self.current_card)
        return card if isinstance(card, disnake.Embed) else list(self.cards_map.values())[0]

    def create_cards_map(self):
        game = self.game
        game_data = game.game_data
        self.cards_map = {
            t('event_card'): game_data.event_embed,
            **{
                t('player_card', player=(player_to_member(self.guild, player).display_name)): game_data.create_player_embed(game_data.hidden_data[player]) # type: ignore <- player is not None
                for player in game.players if player.player_id != game.master.player_id
            }
        }

    async def update_using(self, inter: disnake.MessageInteraction):
        self.create_cards_map()
        self._update_components()
        await inter.response.edit_message(embed=self.create_embed(), view=self)

    def _update_components(self) -> None:
        for component in self._updateable_components:
            component.update()

    async def message_update(self):
        self.create_cards_map()
        self._update_components()
        await self.message.edit(embed=self.create_embed(), view=self)




