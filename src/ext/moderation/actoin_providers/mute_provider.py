from src.ext.moderation.actoin_providers.base import (TemporaryActionProvider,
                                                      ActionProvider)


class MuteProvider(TemporaryActionProvider):
    @property
    def action_name(self) -> str:
        return 'mute'

    async def make_discord_action(self) -> None:
        await self.target_as_member.timeout(
            duration=self._time,
            reason=self._reason,
        )


class UnmuteProvider(ActionProvider):
    @property
    def action_name(self) -> str:
        return 'unmute'

    async def make_discord_action(self) -> None:
        await self.target_as_member.timeout(
            duration=None,
            reason=self._reason,
        )
