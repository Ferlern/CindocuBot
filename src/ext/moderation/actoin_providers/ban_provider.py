from typing import Literal
import disnake

from src.ext.moderation.actoin_providers.base import ActionProvider


class BanProvider(ActionProvider):
    def __init__(
        self,
        author: disnake.Member,
        target: disnake.abc.Snowflake,
        reason: str,
        delete_days: Literal[0, 1, 2, 3, 4, 5, 6, 7] = 0,
    ) -> None:
        super().__init__(author, target, reason)
        self._delete_days = delete_days

    @property
    def action_name(self) -> str:
        return 'ban'

    async def make_discord_action(self) -> None:
        await self._author.guild.ban(
            self._target,
            reason=self._reason,
            delete_message_days=self._delete_days,  # type: ignore
        )


class UnbanProvider(ActionProvider):
    @property
    def action_name(self) -> str:
        return 'unban'

    async def make_discord_action(self) -> None:
        await self._author.guild.unban(
            self._target,
            reason=self._reason,
        )
