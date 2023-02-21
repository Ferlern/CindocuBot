import disnake

from src.bot import SEBot
from src.logger import get_logger
from src.translation import get_translator
from src.discord_views.embeds import DefaultEmbed
from src.ext.game.services.games import DiceGame
from src.ext.game.utils import user_to_player
from src.formatters import to_mention, ordered_list
from .single import SingleDiscordInterface


logger = get_logger()
t = get_translator(route='ext.games')


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
