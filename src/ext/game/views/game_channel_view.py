import disnake

from src.discord_views.embeds import DefaultEmbed
from src.translation import get_translator
from src.logger import get_logger
from src.ext.game.views.game_interfaces.channel_base import ChannelGameInterface
from src.ext.game.services.game_channel import GameChannel
from src.ext.game.db_services import get_game_channel_settings

logger = get_logger()
t = get_translator(route="ext.games")

class GameChannelView(disnake.ui.View):
    def __init__(
        self,
        guild: disnake.Guild,
        voice_category: disnake.CategoryChannel,
        game_channel: GameChannel,
        interface_type: type[ChannelGameInterface],
        *,
        timeout = None
    ) -> None:
        super().__init__(timeout=timeout)
        self.guild = guild
        self.voice_category = voice_category
        self.game_channel = game_channel
        self.interface_type = interface_type

        self.add_item(GameChannelPlayButton())
        self.add_item(RulesButton())

    async def update_or_create_channel_message(self) -> None:
        game_channel = self.game_channel
        channel = game_channel.channel
        message = game_channel.message

        if message:
            logger.debug('game message already on channel: %s in guild %s', channel.name, channel.guild.name)
            await message.edit(view=self)
            return

        logger.debug('sending interactive game message on channel: %s in guild %s', channel.name, channel.guild.name)
        created_message = await channel.send(embed=self.create_embed(), view=self)
        self.create_game_channel_message(created_message.id)

    def create_embed(self) -> disnake.Embed:
        game_channel = self.game_channel
        game_name = game_channel.game_name
        embed = DefaultEmbed(
            title=':boom:' + ' ' + t(game_name),
            description=t(f'{game_name}_desc')
        )
        embed.set_image(url=game_channel.game_settings.channel_art)
        return embed
    
    def create_game_channel_message(self, created_message_id):
        settings = get_game_channel_settings(self.guild.id)
        settings.messages_id[self.game_channel.game_name] = created_message_id # type: ignore
        settings.save()

class RulesButton(disnake.ui.Button):
    view: GameChannelView

    def __init__(self) -> None:
        super().__init__(
            label=t('game_rules'),
            style=disnake.ButtonStyle.blurple
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.send_message(
            embed=DefaultEmbed(
                description=self.view.game_channel.game_settings.rules
            ), ephemeral=True)


class GameChannelPlayButton(disnake.ui.Button):
    view: GameChannelView

    def __init__(self) -> None:
        super().__init__(
            label=t('play_game'),
            style=disnake.ButtonStyle.green
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        from .find_or_create_voice_game_channel import FindOrCreateVoiceGameChannelView

        view = self.view
        voice_inter = FindOrCreateVoiceGameChannelView(
            view.guild,
            view.game_channel,
            view.interface_type,
            view.voice_category
        )

        await interaction.response.defer()
        await interaction.followup.send(
            embed=voice_inter.create_embed(),
            view=voice_inter,
            ephemeral=True
        )
