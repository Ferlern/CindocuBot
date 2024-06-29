from __future__ import annotations
from typing import TYPE_CHECKING
import disnake

from src.bot import SEBot
from src.logger import get_logger
from src.translation import get_translator
from src.ext.game.utils import player_to_member
from src.ext.game.services.games.bunker import BunkerGame
from .vote import VoteInterface
from .bunker_base import BunkerGameInterface
from src.ext.game.views.bunker_views import SubmitAttributeButton, ExcludeButton, PlayerSelect, AttributeSelect, AddPlayerToVote, StartVoteButton

if TYPE_CHECKING:
    from .bunker import BunkerDiscordInterface

logger = get_logger()
t = get_translator(route='ext.games')

class MasterPanelInterface(BunkerGameInterface):
    def __init__(
        self,
        bot: SEBot,
        guild: disnake.Guild,
        message: disnake.Message,
        game: BunkerGame,
        view: BunkerDiscordInterface,
        *,
        timeout = None,
    ) -> None:
        super().__init__(bot, guild, message, game, timeout=timeout)
        self.main_interface = view
        self.vote_interface = VoteInterface(self.bot, self.guild, self.game, self.message)        
        self.create_players_map()
        self.current_card = list(self.players_map)[0]
        self.current_player = list(self.players_map.values())[0][0]
        self.create_attributes_map()
        self.current_attribute: tuple = (None, None)

        player_select = PlayerSelect()
        attribute_select = AttributeSelect()
        self.add_item(player_select)
        self.add_item(attribute_select)
        self.add_item(SubmitAttributeButton())
        self.add_item(ExcludeButton())
        self.add_item(AddPlayerToVote())
        self.add_item(StartVoteButton())

        self._updateable_components = [player_select, attribute_select]
        self._update_components()

    def create_embed(self) -> disnake.Embed:
        card_data = self.players_map.get(self.current_card)

        if card_data is not None and isinstance(card_data[1], disnake.Embed):
            return card_data[1]

        return list(self.players_map.values())[0][1]

    def create_players_map(self):
        game = self.game
        self.players_map = {
            t('player_card', player=(player_to_member(self.guild, player).display_name)): ( # type: ignore <- player is not None
                player, game.game_data.players_embeds[player],
            ) for player in game.players if player.player_id != game.master.player_id
        }

    def create_attributes_map(self):
        game_data = self.game.game_data
        cur_player = self.current_player
        player_fields = game_data.make_data_fields(cur_player)[:-1]
        hidden_fields = game_data.hidden_data[cur_player]

        fields = {field[0]: field for field in player_fields if field not in hidden_fields}
        self.attributes_map = {t('no_attributes_left'): None} if not fields else fields

    async def update_using(self, inter: disnake.MessageInteraction):
        self.create_players_map()
        self.create_attributes_map()
        self._update_components()
        await inter.response.edit_message(embed=self.create_embed(), view=self)

    def _update_components(self) -> None:
        for component in self._updateable_components:
            component.update()
