import disnake
from disnake.ext import commands
from datetime import datetime
import dateparser
import requests
from io import BytesIO
from typing import Optional, Union

from src.bot import SEBot
from src.ext.events.server_events import ServerEvents, EventType
from src.discord_views.base_view import BaseView
from src.discord_views.shortcuts import request_data_via_modal
from src.utils.slash_shortcuts import only_admin
from src.logger import get_logger
from src.translation import get_translator
from .services import get_events_settings

logger = get_logger()
t = get_translator(route='ext.events')


class EventsCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot

    @commands.slash_command(**only_admin)
    async def create_event(
        self,
        inter: disnake.GuildCommandInteraction,
        event_type: str = commands.Param(
            choices={event.get_event_option(): 
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
        event = type.value
        modal_data = await request_data_via_modal(
            inter, t('event_set'), type.get_modal_params() # type: ignore
        )
        settings = get_events_settings(inter.guild.id)
        await inter.response.defer(with_message=False)

        notification_channel = self.bot.get_channel(settings.notification_channel) # type: ignore
        if not isinstance(notification_channel, disnake.TextChannel):
            logger.error("can not get notification channel id")
            return
        
        event_time=_parse_event_time(modal_data[1])
        if not event_time:
            await inter.followup.send(t('wrong_date'), ephemeral=True)
            return 
        
        event_channel = _get_event_channel(self.bot, modal_data[-1], settings.event_channel) # type: ignore
        if not event_channel:
            await inter.followup.send(t('wrong_channel_id'), ephemeral=True)
            return
        
        event_gif = event.gif if event.is_concrete else _fix_gif_url(modal_data[3])
        if not (_check_gif_availability(event_gif)):
            await inter.followup.send(t('wrong_gif'), ephemeral=True)
            return

        event_description = _get_event_long_desc(
            event, modal_data, event_channel.id
        )
                
        event_embed = disnake.Embed(
            color = 0x2c2f33,
            title = t('event_create'),
            description = event_description
        )
        event_embed.set_image(event_gif)
        await inter.followup.send(
            embed=event_embed,
            view=EventView(
                bot = self.bot,
                event = event,
                event_time = event_time,
                notification_channel = notification_channel,
                event_channel = event_channel,
                event_addition_name = modal_data[2] if not event.is_concrete else None
            )
        )

class EventView(BaseView):
    def __init__(
        self,
        bot: SEBot,
        event: EventType,
        event_time: datetime,
        notification_channel: disnake.TextChannel,
        event_channel: disnake.abc.GuildChannel,
        event_addition_name: Optional[str]
    ) -> None:
        super().__init__(
            timeout=180
        )
        self.bot = bot,
        self.event = event
        self.event_time = event_time
        self.notification_channel = notification_channel
        self.event_channel = event_channel
        self.event_addition_name = event_addition_name

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
        event = view.event

        notification_message = await self.view.notification_channel.send(embed=interaction.message.embeds[0])
        await interaction.guild.create_scheduled_event( # type: ignore
            name=t(event.event) if event.is_concrete else view.event_addition_name, # type: ignore
            channel=view.event_channel,
            scheduled_start_time=view.event_time,   
            description=event.get_short_desc(jump_url=notification_message.jump_url),
            image=_get_image_bytes(event.image)
        )
        logger.info("server event created in %d", interaction.guild_id)
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

def _parse_event_time(date_str: str) -> Optional[datetime]:
    event_time = dateparser.parse(date_str, settings={
        'PREFER_DATES_FROM': 'future',
        'TO_TIMEZONE': "ART"
    })
    return event_time if isinstance(event_time, datetime) else None

def _get_event_channel(
        bot: SEBot,
        channel_id: str,
        default_channel_id: int
    ) -> Union[disnake.VoiceChannel, disnake.StageChannel, None]:
    event_channel_id = int(channel_id) if channel_id else default_channel_id
    event_channel = bot.get_channel(event_channel_id)
    if isinstance(event_channel, (disnake.VoiceChannel, disnake.StageChannel)):
        return event_channel
    return None

def _get_event_long_desc(
        event: EventType,
        modal_data,
        event_channel_id: int
    ) -> str:
    if event.is_concrete:
        return event.get_long_desc(
            event_time=modal_data[1] + " МСК",
            event_channel=event_channel_id
        )
    return event.get_long_desc(
        event_addition_name=modal_data[2],
        event_time=modal_data[1] + " МСК",
        event_channel=event_channel_id
    )

def _check_gif_availability(gif_url: str) -> bool:
    try:
        response = requests.get(gif_url)
        return response.status_code // 100 == 2
    except:
         return False

def _fix_gif_url(url: str) -> str:
    return url if '.gif' in url else url + '.gif'
    
def _get_image_bytes(image_url: str) -> bytes:
    response = requests.get(image_url)
    response.raise_for_status()
    image_bytes = BytesIO(response.content).getvalue()
    return image_bytes

def setup(bot) -> None:
    bot.add_cog(EventsCog(bot))
