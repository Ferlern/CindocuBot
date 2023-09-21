import asyncio
from dataclasses import dataclass
import re
import disnake
from disnake.ext import commands
from peewee import DoesNotExist

from src.bot import SEBot
from src.utils.slash_shortcuts import only_admin
from src.utils.counter import Counter
from src.database.services import create_related
from src.database.models import psql_db, Guilds, Puzzles
from src.ext.economy.services import change_balance
from src.logger import get_logger
from src.translation import get_translator


logger = get_logger()

CHANNEL = 968239920521052241
MESSAGES_TIMER = 60  # 60
PUZZLE_TIMEOUT = 600  # 600
PUZZLE_DELAY = 3600  # 3600
MESSAGES_COUNT = 10  # 10
t = get_translator(route='ext.fun')


@dataclass
class DiscordPuzzle:
    message: disnake.Message
    remove_unsolved_task: asyncio.Task
    puzzle: Puzzles


class PuzzleCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot
        self._current_discord_puzzles: dict[disnake.Guild, DiscordPuzzle] = {}
        self._message_counters: dict[disnake.Guild, Counter] = {}

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        author = message.author
        if author.bot or not isinstance(author, disnake.Member):
            return

        guild: disnake.Guild = message.guild  # type: ignore
        discord_puzzle = self._current_discord_puzzles.get(guild)

        if discord_puzzle:
            puzzle, puzzle_message = discord_puzzle.puzzle, discord_puzzle.message
            if message.content not in puzzle.answers:
                logger.debug("puzzle exists on guild %s but asnwer is wrong", guild.id)
                return

            logger.debug("puzzle exists on guild %s and asnwer is right", guild.id)
            # TODO send message to user
            asyncio.create_task(message.channel.send(t('puzzle_right_answer'), reference=message))
            asyncio.create_task(puzzle_message.delete())
            discord_puzzle.remove_unsolved_task.cancel()
            del self._current_discord_puzzles[guild]
            Puzzles.delete().where(Puzzles.id == puzzle.id).execute()
            change_balance(guild.id, author.id, puzzle.prize)
            return

        counter = self._message_counters.setdefault(
            guild, Counter(MESSAGES_TIMER, MESSAGES_COUNT, PUZZLE_DELAY)
        )
        counter.add()
        if not counter.ready:
            logger.debug("puzzle counter on guild %s not ready", guild.id)
            return

        try:
            puzzle = Puzzles.get(Puzzles.guild == guild.id)
        except DoesNotExist:
            logger.debug("puzzle counter on guild %s ready, but no puzzle in db", guild.id)
            counter.remove_delay()
            return

        logger.debug("sending puzzle on guild %s", guild.id)
        puzzle_message = await message.channel.send(puzzle.text)

        task = asyncio.create_task(self._remove_unsolved_puzzle(puzzle_message))
        self._current_discord_puzzles[guild] = DiscordPuzzle(
            puzzle_message,
            task,
            puzzle,
        )

    @commands.slash_command(**only_admin)
    async def add_puzzle(
        self,
        inter: disnake.GuildCommandInteraction,
        text: str,
        answers: str,
        prize: int = 100,
    ) -> None:
        """
        Выполнить действие

        Parameters
        ----------
        text: Текст загадки
        answers: Возможные ответы (указывать через запятую)
        prize: Приз за решение загадки
        """
        asyncio.create_task(
            create_puzzle(inter.guild_id, text, re.split(r', |,', answers), prize)
        )
        asyncio.create_task(inter.response.send_message(t('puzzle_created')))

    async def _remove_unsolved_puzzle(self, message: disnake.Message) -> None:
        logger.debug("Start remove unsolved puzzle")
        await asyncio.sleep(PUZZLE_TIMEOUT)
        logger.debug("Remove unsolved puzzle")
        del self._current_discord_puzzles[message.guild]  # type: ignore
        await message.delete()


@create_related(Guilds)
@psql_db.atomic()
async def create_puzzle(
    guild_id: int,
    /,
    text: str,
    answers: list[str],
    prize: int,
) -> None:
    Puzzles.create(
        guild=guild_id,
        text=text,
        answers=answers,
        prize=prize
    )


def setup(bot) -> None:
    bot.add_cog(PuzzleCog(bot))
