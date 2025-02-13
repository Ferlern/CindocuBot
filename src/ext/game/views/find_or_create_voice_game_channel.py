import asyncio
import disnake

from src.translation import get_translator
from src.logger import get_logger
from src.discord_views.embeds import DefaultEmbed
from src.ext.game.views.game_interfaces.channel_base import ChannelGameInterface
from src.ext.game.services.game_channel import GameChannel
from src.ext.game.services.voice_channel import VoiceGameChannel
from src.ext.game.views.channel_start import VoiceGameStart


logger = get_logger()
t = get_translator(route="ext.games")

HIDE_VOICE_GAMES_AFTER = 15
MAX_GAME_CHANNELS_AT_A_TIME = 7

class FindOrCreateVoiceGameChannelView(disnake.ui.View):
    def __init__(
        self,
        guild: disnake.Guild,
        game_channel: GameChannel,
        interface_type: type[ChannelGameInterface],
        voice_category: disnake.CategoryChannel
    ) -> None:
        super().__init__(timeout=None)
        self.guild = guild
        self.game_channel = game_channel
        self.interface_type = interface_type
        self.voice_category = voice_category

        self.add_item(CreateGameButton())
        self.add_item(FindGameButton())

    def create_embed(self) -> disnake.Embed:
        return DefaultEmbed(
            title=t('lobby'),
            description=t('lobby_desc')
        )

    def create_updated_embed(self, title: str, desc: str) -> disnake.Embed:
        return DefaultEmbed(
            title=title,
            description=desc
        )

    def create_embed_parts(self, channels: list[VoiceGameChannel]) -> tuple[str, str]:        
        available_channels = '\n\n'.join(
            [f"{channel.jump_url} ({len(channel)}/{channel.user_limit})" 
             for channel in channels]
        )
        channels_count = len(channels)

        title = t('found_games', count=channels_count)
        desc = f"**Каналы:**\n{available_channels}" if channels_count else t('create_yourself')
        return (title, desc)


class CreateGameButton(disnake.ui.Button):
    view: FindOrCreateVoiceGameChannelView

    def __init__(self) -> None:
        super().__init__(
            label=t('create_game'),
            style=disnake.ButtonStyle.green
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        view = self.view
        player = interaction.user

        if not isinstance(player, disnake.Member):
            return

        guild = view.guild
        voice_category = view.voice_category
        game_channel = view.game_channel
        interface_type = view.interface_type

        if len(voice_category.voice_channels) >= MAX_GAME_CHANNELS_AT_A_TIME:
            await interaction.response.send_message(t('too_much_lobbies'), ephemeral=True)
            return

        channel_name = f"{t(game_channel.game_name)} - {player.display_name}"
        user_limit = game_channel.game_settings.max_players
        channel = await voice_category.create_voice_channel(name=channel_name, user_limit=user_limit)
        await channel.set_permissions(player, view_channel=True, connect=True, move_members=True)

        v_channel = VoiceGameChannel(guild, voice_category, channel, game_channel.game_settings, interface_type)
        view.game_channel.voice_channels.append(v_channel)
        game_start_message = VoiceGameStart(view.guild, v_channel)

        await asyncio.gather(
                game_start_message.create_message(),
                interaction.response.edit_message(
                    embed=view.create_updated_embed(
                        t('game_created'), t('game_connect', jump_url=channel.jump_url)
                    ), view=view
                ))


class FindGameButton(disnake.ui.Button):
    view: FindOrCreateVoiceGameChannelView

    def __init__(self) -> None:
        super().__init__(
            label=t('find_game'),
            style=disnake.ButtonStyle.blurple
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        view = self.view
        voice_category = view.voice_category
        if not isinstance(voice_category, disnake.CategoryChannel):
            return
        player = interaction.user
        if not isinstance(player, disnake.Member):
            return

        game_channels = [channel for channel in view.game_channel.voice_channels if channel.is_connectable]
        voice_channels = [channel.channel for channel in game_channels]
        await self._show_voice_channels(player, voice_channels)

        await interaction.response.edit_message(
            embed=view.create_updated_embed(*view.create_embed_parts(game_channels)),
            view=view
        )

        await asyncio.sleep(HIDE_VOICE_GAMES_AFTER)
        await self._hide_voice_channels(player, voice_channels)

    async def _show_voice_channels(self, player: disnake.Member, channels: list[disnake.VoiceChannel]) -> None:
        tasks = [channel.set_permissions(player, view_channel=True, connect=True) for channel in channels]
        await asyncio.gather(*tasks)

    async def _hide_voice_channels(self, player: disnake.Member, channels: list[disnake.VoiceChannel]) -> None:
        if player.voice and player.voice.channel in self.view.voice_category.voice_channels:
            tasks = [channel.set_permissions(player, view_channel=False) for channel in channels if not channel == player.voice.channel]
            await asyncio.gather(*tasks)
            return

        tasks = [channel.set_permissions(player, view_channel=False) for channel in channels]
        await asyncio.gather(*tasks)