import asyncio
from dataclasses import dataclass
import itertools
import re
import disnake
from disnake.ext import commands
from peewee import DoesNotExist
from typing import Optional
import requests

from src.bot import SEBot
from src.utils.slash_shortcuts import only_admin
from src.utils.counter import Counter
from src.database.services import create_related
from src.database.models import psql_db, Guilds, Puzzles
from src.ext.economy.services import change_balance, get_economy_settings
from src.logger import get_logger
from src.translation import get_translator


logger = get_logger()

CHANNEL = 968239920521052241
MESSAGES_TIMER = 60  # 60
PUZZLE_TIMEOUT = 600  # 600
PUZZLE_DELAY = 3600  # 3600
MESSAGES_COUNT = 10  # 10
IMAGES_CYCLE = itertools.cycle((
    "https://i.pinimg.com/originals/c1/dc/10/c1dc10bb56883a1b134e50305abe10b8.gif",
    "https://i.pinimg.com/originals/df/ff/8f/dfff8f4a814276130f1bdbb74a5c3a45.gif",
    "https://i.pinimg.com/originals/2e/6d/cb/2e6dcb397d31d7fde0f1a58b3daeb543.gif",
    "https://i.pinimg.com/originals/f6/95/e7/f695e77ed1b45c3c55d77996b9b136fe.gif",
    "https://i.pinimg.com/originals/72/67/03/726703ed24cb298eddd25ee9f8da00db.gif",
    "https://i.pinimg.com/originals/9b/36/64/9b3664015c7e18a503d10f80e1062695.gif",
))
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
        if author.bot or not isinstance(author, disnake.Member) or message.channel.id != CHANNEL:
            return

        guild: disnake.Guild = message.guild  # type: ignore
        settings = get_economy_settings(guild.id)
        discord_puzzle = self._current_discord_puzzles.get(guild)

        if discord_puzzle:
            puzzle, puzzle_message = discord_puzzle.puzzle, discord_puzzle.message
            if message.content not in puzzle.answers:
                logger.debug("puzzle exists on guild %s but asnwer is wrong", guild.id)
                return

            logger.debug("puzzle exists on guild %s and asnwer is right", guild.id)
            # TODO send message to user
            asyncio.create_task(
                message.channel.send(
                    embed=disnake.Embed(
                        title=t("puzzle_right_answer_title"),
                        description=t(
                            "puzzle_right_answer_desc",
                            prize=puzzle.prize,
                            coin=settings.coin,
                        ),
                        color=0x2c2f33,
                    ),
                    reference=message
                )
            )
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
        embed = disnake.Embed(
            title=t("puzzle_title"),
            description=t(
                "puzzle_desc",
                prize=puzzle.prize,
                coin=settings.coin,
            ) + f"\n\n{puzzle.text}",
            color=0x2c2f33,
        )
        embed.set_image(next(IMAGES_CYCLE) if puzzle.image_url is None else puzzle.image_url)
        puzzle_message = await message.channel.send(
            embed=embed
        )

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
        image_url: Optional[str] = None,
        prize: int = 100,
    ) -> None:
        """
        Выполнить действие

        Parameters
        ----------
        text: Текст загадки (\\n для переноса строки)
        answers: Возможные ответы (указывать через запятую)
        image_url: Ссылка на картинку
        prize: Приз за решение загадки
        """
        text = text.replace('\\n', '\n')

        created_puzzle_embed = disnake.Embed(
            title=t('created_puzzle_title'),
            description=t(
                'created_puzzle_desc',
                prize=prize,
                answers=answers
            ) + f"\n\n{text}",
            color=0x2c2f33,
        )

        if not image_url:
            asyncio.create_task(create_puzzle(inter.guild_id, text, re.split(r', |,', answers), None, prize))
            asyncio.create_task(inter.response.send_message(embed=created_puzzle_embed))
            return

        url = self._fix_image_url(image_url)
        is_image = self._check_for_correct_url(url)

        if not is_image:
            asyncio.create_task(inter.response.send_message(t('invalid_link'), ephemeral=True))
            return

        asyncio.create_task(create_puzzle(inter.guild_id, text, re.split(r', |,', answers), url, prize))
        created_puzzle_embed.set_image(url=url)
        asyncio.create_task(inter.response.send_message(embed=created_puzzle_embed))

    async def _remove_unsolved_puzzle(self, message: disnake.Message) -> None:
        logger.debug("Start remove unsolved puzzle")
        await asyncio.sleep(PUZZLE_TIMEOUT)
        logger.debug("Remove unsolved puzzle")
        del self._current_discord_puzzles[message.guild]  # type: ignore
        await message.delete()

    def _fix_image_url(self, url) -> str:
        return url if any(ext in url for ext in ['.jpg', '.jpeg', '.png', '.gif',]) else url + '.jpg'
    
    def _check_for_correct_url(self, url) -> bool:
        try:
            response = requests.get(url)
            return response.status_code == 200
        except:
            return False


@create_related(Guilds)
@psql_db.atomic()
async def create_puzzle(
    guild_id: int,
    /,
    text: str,
    answers: list[str],
    image_url: Optional[str],
    prize: int,
) -> None:
    Puzzles.create(
        guild=guild_id,
        text=text,
        answers=answers,
        image_url=image_url,
        prize=prize
    )


def setup(bot) -> None:
    bot.add_cog(PuzzleCog(bot))
