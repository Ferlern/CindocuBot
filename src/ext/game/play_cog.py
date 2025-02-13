import disnake
from disnake.ext import commands

from src.converters import not_self_member
from src.translation import get_translator
from src.logger import get_logger
from src.bot import SEBot
from src.ext.game.services.games import DiceGame
from src.ext.game.views.game_interfaces import DiceDiscordInterface
from src.ext.game.services.lobby import Lobby
from src.ext.game.views.lobby_view import LobbyView
from src.ext.game.utils import user_to_player


logger = get_logger()
t = get_translator(route="ext.games")
GAMES_MAPPING = games_mapping = {
    t('dice_game'): (DiceGame, DiceDiscordInterface),
}


class PlayCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot

    @commands.slash_command()
    async def play(
        self,
        inter: disnake.GuildCommandInteraction,
        bet: commands.Range[25, ...],
        game: str = commands.Param(choices=list(GAMES_MAPPING.keys())),
        player: disnake.Member = commands.Param(default=None, converter=not_self_member),
    ) -> None:
        """
        Сыграть в игру на деньги

        Parameters
        ----------
        bet: Ставка, которую будет обязан сделать каждый участвующий
        game: Игра
        player: Приглашённый игрок. Он сможет присоединиться, даже если лобби будет закрыто
        """
        (game_type, interface_type) = GAMES_MAPPING[game]
        discord_game = game_type()

        lobby = Lobby(inter.guild.id, bet, discord_game, user_to_player(inter.author))
        lobby.add(user_to_player(inter.author))
        if player:
            lobby.invite(user_to_player(player))

        view = LobbyView(inter.guild, lobby, game, interface_type)
        await view.start_from(inter)


def setup(bot) -> None:
    bot.add_cog(PlayCog(bot))
