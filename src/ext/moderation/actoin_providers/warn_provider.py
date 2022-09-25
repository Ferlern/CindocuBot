import disnake

from src.database.services import get_member
from src.translation import get_translator
from src.logger import get_logger
from src.discord_views.embeds import DefaultEmbed
from src.ext.moderation.services import (add_warn, remove_warn,
                                         get_moderation_settings)
from src.ext.moderation.actoin_providers.base import ActionProvider
from src.ext.moderation.actoin_providers.mute_provider import MuteProvider
from src.ext.moderation.actoin_providers.ban_provider import BanProvider


t = get_translator(route='ext.moderation')
logger = get_logger()


class WarnProvider(ActionProvider):
    def __init__(
        self,
        author: disnake.Member,
        target: disnake.abc.Snowflake,
        reason: str,
    ) -> None:
        super().__init__(author, target, reason)
        guild_id = author.guild.id
        settings = get_moderation_settings(guild_id)
        member_data = get_member(guild_id, target.id)

        warn_info = settings.warns_system.get(  # type: ignore
            str(member_data.warns)
        )
        self._additional_text = warn_info['text'] if warn_info else None
        mute_time = warn_info['mute_time'] if warn_info else None
        ban = warn_info['ban'] if warn_info else None

        discord_action_provider = None
        additional_action_reason = t(
            'warn_additional_action_rason',
            count=member_data.warns
        )
        if ban:
            discord_action_provider = BanProvider(
                author, target, additional_action_reason,
            )
        elif mute_time:
            discord_action_provider = MuteProvider(
                author, target, additional_action_reason,
                mute_time,  # type: ignore
            )
        self._discord_action_provider = discord_action_provider

    @property
    def action_name(self) -> str:
        return 'warn'

    async def send_dm_to_target(self) -> None:
        description = self._get_or_create_description()
        if self._additional_text:
            description += f"\n\n{self._additional_text}"

        embed = DefaultEmbed(
            title=t(f'{self.action_name}_dm'),
            description=description,
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

    async def make_discord_action(self) -> None:
        discord_action_provider = self._discord_action_provider
        if not discord_action_provider:
            return
        await discord_action_provider.make_discord_action()

    async def update_db(self) -> None:
        add_warn(
            self._author.guild.id,
            self._target.id,
        )


class UnwarnProvider(ActionProvider):
    @property
    def action_name(self) -> str:
        return 'unwarn'

    async def make_discord_action(self) -> None:
        # no discord action needed here
        pass

    async def update_db(self) -> None:
        remove_warn(
            self._author.guild.id,
            self._target.id,
        )
