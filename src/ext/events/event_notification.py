import disnake
from disnake.ext import commands
from datetime import datetime
import dateparser
import requests
from io import BytesIO

from src.bot import SEBot
from src.ext.events.server_events import ServerEvents
from src.discord_views.base_view import BaseView
from src.discord_views.shortcuts import request_data_via_modal
from src.utils.slash_shortcuts import only_admin
from src.logger import get_logger
from src.translation import get_translator

logger = get_logger()
t = get_translator(route='ext.events')

NOTIFICATION_CHANNEL_ID = 987069250806095963
EVENT_CHANNEL_ID = 968268849034174524

class EventsCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot

    @commands.slash_command(**only_admin)
    async def create_event(
        self,
        inter: disnake.MessageCommandInteraction,
        event_type: str = commands.Param(
            choices={event.get_translated_name(): 
                     event.name for event in ServerEvents}
        )
    ) -> None:
        """
        Создать упоминание о грядущем ивенте 

        Parameters
        ----------
        event_type: Тип ивента, который будет проходить
        """
        type = ServerEvents[event_type]
        result = await request_data_via_modal(
            inter, t('event_set'), type.get_modal_params()
        )

        await inter.response.defer(with_message=False)

        notification_channel = self.bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if not isinstance(notification_channel, disnake.TextChannel):
            logger.error("can not get notification channel id")
            return
        
        event_time=dateparser.parse(result[1], settings={'PREFER_DATES_FROM': 'future'})
        if not isinstance(event_time, datetime):
            await inter.followup.send(t('wrong_date'), ephemeral=True)
            return 
        
        event_channel = self.bot.get_channel(int(result[2]) if result[2] != '' else EVENT_CHANNEL_ID)
        if not (isinstance(event_channel, disnake.VoiceChannel)
             or isinstance(event_channel, disnake.StageChannel)):
            await inter.followup.send(t('wrong_channel_id'), ephemeral=True)
            return
        
        event_description = t(type.value + '_long_desc', 
            event_time = result[1], 
            event_channel = event_channel.id
        )

        event_embed = disnake.Embed(
            color = 0x2c2f33,
            title = t('event_create'),
            description = event_description
        )
        event_embed.set_image(t(type.value + '_gif'))
        await inter.followup.send(
            embed=event_embed,
            view=EventView(
                bot = self.bot,
                event_type = type.value,
                event_time = event_time,
                notification_channel = notification_channel,
                event_channel = event_channel
            )
        )

class EventView(BaseView):
    def __init__(
        self,
        bot: SEBot,
        event_type: str,
        event_time: datetime,
        notification_channel: disnake.TextChannel,
        event_channel: disnake.abc.GuildChannel,
    ) -> None:
        super().__init__(
            timeout=180
        )
        self.bot = bot,
        self.event_type = event_type
        self.event_time = event_time
        self.notification_channel = notification_channel
        self.event_channel = event_channel

        self.add_item(SubmitEventButton())
        self.add_item(CancelEventButton())

class SubmitEventButton(disnake.ui.Button):
    view: EventView

    def __init__(self) -> None:
        super().__init__(
            style=disnake.ButtonStyle.green,
            label=t('event_submit')
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        view = self.view

        notification_message = await self.view.notification_channel.send(embed=interaction.message.embeds[0])
        await interaction.guild.create_scheduled_event( # type: ignore
            name=t(view.event_type),
            channel=view.event_channel,
            scheduled_start_time=view.event_time,   
            description=t(view.event_type + '_short_desc', jump_url=notification_message.jump_url),
            image=await get_image_bytes(t(view.event_type + '_image'))
        )
        logger.info("event notification created in %d", NOTIFICATION_CHANNEL_ID)

        self.view.stop()
        await interaction.message.delete()
    
class CancelEventButton(disnake.ui.Button):
    view: EventView

    def __init__(self) -> None:
        super().__init__(
            style=disnake.ButtonStyle.red,
            label=t('event_cancel')
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        self.view.stop()
        await interaction.message.delete()

async def get_image_bytes(image_url: str) -> bytes:
    response = requests.get(image_url)
    response.raise_for_status()
    image_bytes = BytesIO(response.content).getvalue()
    return image_bytes

def setup(bot) -> None:
    bot.add_cog(EventsCog(bot))
