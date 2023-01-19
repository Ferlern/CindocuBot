from abc import ABC, abstractmethod

import disnake

from src.discord_views.embeds import DefaultEmbed
from src.translation import get_translator
from src.logger import get_logger
from src.utils.time_ import display_time
from src.custom_errors import RegularException
from src.ext.history.services import make_history


t = get_translator(route='ext.moderation')
logger = get_logger()


class ActionProvider(ABC):
    def __init__(
        self,
        author: disnake.Member,
        target: disnake.abc.Snowflake,
        reason: str,
    ) -> None:
        self._author = author
        self._target = target
        self._reason = reason
        self._last_description: str = ""

    @property
    @abstractmethod
    def action_name(self) -> str:
        pass

    @property
    def target_as_member(self) -> disnake.Member:
        member = self._author.guild.get_member(self._target.id)
        if not member:
            raise RegularException(t('cant_find_target'))

        return member

    async def resolve_interaction(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ) -> None:
        embed = DefaultEmbed(
            title=t(self.action_name),
            description=self._get_or_create_description(),
        )
        await inter.response.send_message(embed=embed, delete_after=30)

    async def full_action(self) -> None:
        await self.send_dm_to_target()
        await self.make_discord_action()
        self.create_history()
        await self.update_db()

    def create_history(self) -> None:
        make_history(
            self._author.guild.id,
            self._author.id,
            name=self.action_name,
            description=self._get_or_create_description(),
        )

    async def send_dm_to_target(self) -> None:
        embed = DefaultEmbed(
            title=t(f'{self.action_name}_dm'),
            description=self._create_dm_description(),
        )
        target = self._author.guild.get_member(self._target.id)
        if not target:
            return

        try:
            await target.send(
                embed=embed,
            )
        except disnake.HTTPException:
            logger.info('failed send DM about moderation action to %d',
                        self._target.id)

    @abstractmethod
    async def make_discord_action(self) -> None:
        pass

    async def update_db(self) -> None:
        pass

    def _get_or_create_description(self) -> str:
        if self._last_description:
            return self._last_description

        description = t(
            f'{self.action_name}_desc',
            target_id=self._target.id,
            moderator_id=self._author.id,
            reason=self._reason,
        )
        self._last_description = description
        return description

    def _create_dm_description(self) -> str:
        return t(
            f'{self.action_name}_dm_desc',
            guild_name=self._author.guild.name,
            moderator_id=self._author.id,
            reason=self._reason,
        )


class TemporaryActionProvider(ActionProvider):
    def __init__(
        self,
        author: disnake.Member,
        target: disnake.abc.Snowflake,
        reason: str,
        time: int,
    ) -> None:
        super().__init__(author, target, reason)
        self._time = time

    def _get_or_create_description(self) -> str:
        if self._last_description:
            return self._last_description

        description = t(
            f'{self.action_name}_desc',
            target_id=self._target.id,
            moderator_id=self._author.id,
            reason=self._reason,
            time=display_time(self._time, full=True),
        )
        self._last_description = description
        return description

    def _create_dm_description(self) -> str:
        return t(
            f'{self.action_name}_dm_desc',
            guild_name=self._author.guild.name,
            moderator_id=self._author.id,
            reason=self._reason,
            time=display_time(self._time, full=True),
        )
