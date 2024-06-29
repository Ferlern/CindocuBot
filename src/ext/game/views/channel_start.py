from asyncio import sleep
import disnake

from src.translation import get_translator
from src.logger import get_logger
from src.ext.game.utils import user_to_player
from src.ext.game.services.voice_channel import VoiceGameChannel
from src.ext.game.services.game_channel import GameChannel

logger = get_logger()
t = get_translator(route="ext.games")

ON_TIMEOUT_CHANNEL_DELETE_TIME = 30

class VoiceGameStart(disnake.ui.View):
    def __init__(
        self,
        guild: disnake.Guild,
        voice_channel: VoiceGameChannel
    ) -> None:
        super().__init__(timeout=300)
        self.guild = guild
        self.voice_channel = voice_channel

        invite_select = InviteSelect()
        open_close_voice_game = OpenCloseVoiceGame()
        self.add_item(invite_select)
        self.add_item(open_close_voice_game)
        self.add_item(StartButton())

        self._updateable_components = [invite_select, open_close_voice_game]
        self._update_components()

    def create_embed(self) -> disnake.Embed:
        return disnake.Embed(
            title="Все готовы?",
            description="Начинает игру ведущий, сменить ведущего во время игры нельзя.", # TODO not every game has master
            color=0x7B68EE
        )
    
    async def update(self) -> None:
        self._update_components()
        message = self.voice_channel.message
        if message:
            await message.edit(embed=self.create_embed(), view=self)

    async def update_using(self, inter: disnake.MessageInteraction) -> None:
        self._update_components()
        await inter.response.edit_message(embed=self.create_embed(), view=self)

    def _update_components(self) -> None:
        for component in self._updateable_components:
            component.update()
    
    async def start_game(self, interaction: disnake.MessageInteraction) -> bool:
        voice_channel = self.voice_channel
        channel = voice_channel.channel
        settings = voice_channel.game_settings
        game = voice_channel.game_settings.game_type()
        interface_type = voice_channel.game_interface

        players_count = len(voice_channel)

        if players_count < (settings.min_players or 2): 
            await interaction.response.send_message(t('cant_start'), ephemeral=True)
            return False

        await channel.edit(user_limit=players_count)
        game.add_players([user_to_player(member) for member in channel.members])
        game.master = user_to_player(interaction.user)
        game.start()
        self.stop()
        await interface_type.start_from(interaction, game)
        return True

    async def create_message(self) -> None:
        game_message = await self.voice_channel.send_message(self)

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if interaction.user not in self.voice_channel.channel.members:
            await interaction.response.send_message(t('not_a_player'), ephemeral=True)
            return False
        return True
    
    async def on_timeout(self) -> None:
        voice_channel = self.voice_channel
        GameChannel.voice_channels.remove(voice_channel)
        try:
            await voice_channel.message.edit(view=None, embed=disnake.Embed(  # type: ignore
                title="Увы...",
                description=t('channel_timeout'),
                color=0x7B68EE
            ))
            await sleep(ON_TIMEOUT_CHANNEL_DELETE_TIME)
            channel = voice_channel.channel
            await channel.delete()
        except:
            logger.error('on_timeouted game channel not found or deleted already')
            return
        

class StartButton(disnake.ui.Button):
    view: VoiceGameStart

    def __init__(self) -> None:
        super().__init__(
            label=t('start_game'),
            style=disnake.ButtonStyle.blurple
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        success = await self.view.start_game(interaction)
        if success: GameChannel.voice_channels.remove(self.view.voice_channel)


class InviteSelect(disnake.ui.UserSelect):
    view: VoiceGameStart

    def __init__(self) -> None:
        super().__init__(placeholder=t('invite_player'))

    def update(self) -> None:
        pass

    async def callback(self, interaction: disnake.MessageInteraction, /) -> None:
        channel = self.view.voice_channel.channel

        member = self.values[0]
        if isinstance(member, disnake.Member):
            await channel.set_permissions(member, view_channel=True)
            await interaction.response.send_message(t('invited'), ephemeral=True)

        await self.view.update()


class OpenCloseVoiceGame(disnake.ui.Button):
    view: VoiceGameStart

    def update(self) -> None:
        is_connectable = self.view.voice_channel.is_connectable
        self.style = disnake.ButtonStyle.green if is_connectable else disnake.ButtonStyle.red
        self.label = t('close_table') if is_connectable else t('open_table')

    async def callback(self, interaction: disnake.MessageInteraction, /) -> None:
        self.view.voice_channel.close_or_open_connection()
        await self.view.update_using(interaction)

