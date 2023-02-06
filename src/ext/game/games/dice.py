import random
from typing import Sequence
import disnake
from src.bot import SEBot
from src.translation import get_translator
from src.formatters import ordered_list, to_mention
from src.discord_views.embeds import DefaultEmbed
from src.ext.game.games.base import (Player, GameState, GameResult, WrongState,
                                     SingleDiscordInterface, user_to_player, Game)


t = get_translator(route='ext.games')


class DiceGame(Game):
    def __init__(self) -> None:
        super().__init__()
        self._players = []
        self.state = GameState.WAIT_FOR_PLAYER
        self.data: dict[Player, int] = {}

    @property
    def result(self) -> GameResult:
        if self.state is not GameState.END:
            raise WrongState("Can't get results for game that not in END state")
        max_value = max(self.data.values())
        winners_data = filter(lambda item: item[1] == max_value, self.data.items())
        winners = [data[0] for data in winners_data]
        losers = list(set(self.players) - set(winners))
        return GameResult(winners, losers)

    def start(self) -> None:
        self.state = GameState.WAIT_FOR_INPUT
        self._check_state()

    def force_end(self) -> None:
        self.state = GameState.END

    def add_players(self, players: Sequence[Player]) -> None:
        for player in players:
            self._players.append(player)
            if player.bot:
                self._add_dice_result(player)
        self._check_state()

    def accept_input(self, player: Player) -> bool:
        if self.state is not GameState.WAIT_FOR_INPUT:
            return False
        if player.bot:
            return False
        if player in self.data:
            return False
        self._add_dice_result(player)
        self._check_state()
        return True

    def _add_dice_result(self, player: Player) -> None:
        self.data[player] = random.randint(2, 12)

    def _check_state(self) -> None:
        if self.state is GameState.WAIT_FOR_PLAYER:
            return
        if len(self._players) == len(self.data) >= 2:
            self.state = GameState.END
            return


class DiceDiscordInterface(SingleDiscordInterface[DiceGame]):
    def __init__(  # pylint: disable=too-many-arguments
        self,
        bot: SEBot,
        guild: disnake.Guild,
        message: disnake.Message,
        game: DiceGame,
        bet: int,
        *,
        timeout: int = 30,
    ) -> None:
        super().__init__(bot, guild, message, game, bet, timeout=timeout)
        self.add_item(ThrowDiceButton())

    def create_embed(self) -> disnake.Embed:
        player_dict = dict.fromkeys(self.game.players, '?')
        plater_data = {item[0]: str(item[1]) for item in self.game.data.items()}
        player_dict.update(plater_data)
        player_dict = sorted(
            player_dict.items(),
            key=lambda item: int(item[1]) if item[1] != '?' else 0
        )[::-1]
        player_desc = ordered_list(
            player_dict, lambda item: f'{to_mention(item[0].player_id)} — {item[1]}'
        )
        return DefaultEmbed(
            title=t('dice_game'),
            description=f"{t('dice_player_results')}\n\n{player_desc}",
        )


class ThrowDiceButton(disnake.ui.Button):
    view: DiceDiscordInterface

    def __init__(self) -> None:
        super().__init__(
            style=disnake.ButtonStyle.blurple,
            label=t('dice_throw_button'),
        )

    async def callback(
        self,
        interaction: disnake.MessageInteraction,
        /,
    ) -> None:
        accepted = self.view.game.accept_input(user_to_player(interaction.author))
        if accepted:
            await interaction.response.edit_message(embed=self.view.create_embed())
        else:
            await interaction.response.send_message(t('dice_already'), ephemeral=True)
