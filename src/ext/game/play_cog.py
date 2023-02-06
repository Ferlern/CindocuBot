import disnake
from disnake.ext import commands

from src.discord_views.embeds import DefaultEmbed
from src.converters import not_self_member
from src.translation import get_translator
from src.logger import get_logger
from src.custom_errors import CriticalException
from src.bot import SEBot
from src.ext.economy.services import change_balance, change_balances
from src.ext.game.games.base import Game, user_to_player, DiscordInterface
from src.ext.game.games.dice import DiceGame, DiceDiscordInterface


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
        bet: int,
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
        invited = [player] if player else []
        view = GameTable(discord_game, game, interface_type, inter.author, bet, invited)
        await view.start_from(inter)


class GameTable(disnake.ui.View):  # noqa
    def __init__(  # noqa
        self,
        game: Game,
        game_name: str,
        interface_type: type[DiscordInterface],
        host: disnake.Member,
        bet: int,
        invited: list[disnake.Member],
    ) -> None:
        super().__init__(timeout=180)
        self.game = game
        self.interface_type = interface_type
        self.host = host
        self.bet = bet
        self.message = None
        self.invited: list[disnake.Member] = invited
        self.open: bool = not invited
        self.players: list[disnake.Member] = [host]
        self._game_name = game_name

        _updateable_components = []
        open_close_button = OpenCloseTableButton()
        kick_select = KickPlayerSelect()

        self.add_item(JoinGameButton())
        self.add_item(StartGameButton())
        self.add_item(open_close_button)
        self.add_item(kick_select)

        _updateable_components.append(open_close_button)
        _updateable_components.append(kick_select)

        self._auto_join_bots()
        self._updateable_components = _updateable_components
        self._update_components()
        change_balance(host.guild.id, host.id, -bet)

    async def update(self) -> None:
        if not self.message:
            raise CriticalException('GameTable has no message during update')
        self._auto_join_bots()
        self._update_components()
        await self.message.edit(embed=self.create_embed(), view=self)

    async def update_using(self, inter: disnake.MessageInteraction) -> None:
        self._auto_join_bots()
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
                game_name=self._game_name,
                host_id=self.host.id,
                players=', '.join([player.mention for player in self.players]),
                bet=self.bet,
                current=len(self.players),
                limit=10,
            ),
        )

    async def on_timeout(self) -> None:
        await self.message.edit(view=None, embed=DefaultEmbed(  # type: ignore
            title=t('table'),
            description=t('timeout'),
        ))
        player_ids = [player.id for player in self.players]
        change_balances(self.host.id, player_ids, self.bet)

    def _update_components(self) -> None:
        for component in self._updateable_components:
            component.update()

    def _auto_join_bots(self) -> None:
        for member in self.invited:
            if member.bot:
                self.invited.remove(member)
                self.players.append(member)


class JoinGameButton(disnake.ui.Button):
    view: GameTable

    def __init__(self) -> None:
        super().__init__(
            style=disnake.ButtonStyle.blurple,
            label=t('join_game'),
        )

    async def callback(self, interaction: disnake.MessageInteraction, /) -> None:
        view = self.view
        players = view.players
        author = interaction.author
        if author in players:
            await interaction.response.send_message(t('already_joined'), ephemeral=True)
            return
        if view.open is False and author not in view.invited:
            await interaction.response.send_message(t('table_closed'), ephemeral=True)
            return
        # Large number of players can provoke a lot of issues such as reaching max embed size
        # or reaching the rate limit of discord actions
        if len(players) >= 10:
            await interaction.response.send_message(t('max_players'), ephemeral=True)
            return

        # hold money to be sure that member will not transfer it during the game session
        # NotEnoughMoney will be raised if member don't have enough money so this line should
        # stay before any other valuable actions
        change_balance(view.host.guild.id, author.id, -self.view.bet)
        players.append(interaction.author)  # type: ignore
        await view.update_using(interaction)


class StartGameButton(disnake.ui.Button):
    view: GameTable

    def __init__(self) -> None:
        super().__init__(
            style=disnake.ButtonStyle.green,
            label=t('start_game'),
        )

    async def callback(self, interaction: disnake.MessageInteraction, /) -> None:
        view = self.view
        players = view.players
        if view.host != interaction.author:
            await interaction.response.send_message(
                t('not_a_host', user_id=view.host.id), ephemeral=True,
            )
            return
        game = view.game
        if len(players) < 2:
            await interaction.response.send_message(t('cant_start'), ephemeral=True)
            return
        game.add_players(list(map(user_to_player, players)))
        game.start()
        view.stop()
        await view.interface_type.start_from(interaction, view.game, view.bet)


class OpenCloseTableButton(disnake.ui.Button):
    view: GameTable

    def update(self) -> None:
        is_open = self.view.open
        self.style = disnake.ButtonStyle.green if is_open else disnake.ButtonStyle.red
        self.label = t('close_table') if is_open else t('open_table')

    async def callback(self, interaction: disnake.MessageInteraction, /) -> None:
        host = self.view.host
        if host != interaction.author:
            await interaction.response.send_message(
                t('not_a_host', user_id=host.id), ephemeral=True,
            )
            return
        self.view.open = not self.view.open
        await self.view.update_using(interaction)


class KickPlayerSelect(disnake.ui.Select):
    view: GameTable

    def __init__(self) -> None:
        super().__init__(placeholder=t('kick_player'))

    def update(self) -> None:
        self.options = [disnake.SelectOption(
            label=str(player), value=str(player.id)
        ) for player in self.view.players]

    async def callback(self, interaction: disnake.MessageInteraction, /) -> None:
        players_to_kick = interaction.values
        if not players_to_kick:
            await self.view.update_using(interaction)
            return

        host = self.view.host
        guild = host.guild
        kicked_ids: list[int] = []
        for strid in players_to_kick:
            member = guild.get_member(int(strid))
            if not member or member == self.view.host.id or member not in self.view.players:
                continue
            kicked_ids.append(member.id)
            self.view.players.remove(member)
            # TODO interface should be notified about player remove

        await self.view.update_using(interaction)
        if kicked_ids:
            # return bet to users
            change_balances(guild.id, kicked_ids, self.view.bet)


def setup(bot) -> None:
    bot.add_cog(PlayCog(bot))
