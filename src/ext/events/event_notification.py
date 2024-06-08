import disnake
from disnake.ext import commands

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
        event_type=commands.Param(
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
        channel = self.bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if not isinstance(channel, disnake.TextChannel):
            return

        event_description = t(type.value + '_description', 
                    event_time = result[1], 
                    event_channel = result[2] if result[2] != '' else EVENT_CHANNEL_ID
                )

        event_embed = disnake.Embed(
            color = 0x2c2f33,
            title = t('event_create'),
            description = event_description
        )
        event_embed.set_image(t(type.value + '_gif'))
        await inter.response.send_message(embed=event_embed, view=EventView(channel))

class EventView(BaseView):
    def __init__(self, channel: disnake.TextChannel) -> None:
        super().__init__(
            timeout=180
        )
        self.channel = channel

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
        await self.view.channel.send(embed=interaction.message.embeds[0])
        await interaction.message.delete()
    
class CancelEventButton(disnake.ui.Button):
    view: EventView

    def __init__(self) -> None:
        super().__init__(
            style=disnake.ButtonStyle.red,
            label=t('event_cancel')
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        await interaction.message.delete()

def setup(bot) -> None:
    bot.add_cog(EventsCog(bot))