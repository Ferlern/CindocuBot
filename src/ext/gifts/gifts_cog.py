import disnake
from disnake.ext import commands
from enum import Enum

from src.bot import SEBot
from src.discord_views.embeds import DefaultEmbed
from src.discord_views.base_view import BaseView
from src.translation import get_translator
from src.logger import get_logger
from src.ext.gifts.services import (
    get_gifts,
    get_activity_presents,
    add_activity_present
)
from src.ext.gifts.presents import ActivityPresent, AnotherPresent
from src.ext.activity.services import get_voice_rewards_settings
from src.formatters import ordered_list
from src.utils.slash_shortcuts import only_admin
from src.converters import not_bot_member


logger =  get_logger()
t = get_translator(route='ext.gifts')


class PresentsMap(str, Enum):
    ACTIVITY_PRESENT = "activity present"
    ANOTHER_PRESENT = "another present"

    def get_present(self):
        return {
            PresentsMap.ACTIVITY_PRESENT: ActivityPresent,
            PresentsMap.ANOTHER_PRESENT: AnotherPresent
        }[self]


class GiftsCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot

    @commands.slash_command()
    async def gifts(self, interaction: disnake.GuildCommandInteraction) -> None:
        """
        Просмотр и открытие полученных подарков
        """
        guild = interaction.guild
        user = interaction.user
        view = GiftsView(guild.id, user.id)
        await view.start_from(interaction)

    @commands.slash_command(**only_admin)
    async def give_act_gifts(
        self,
        inter: disnake.GuildCommandInteraction,
        amount: int,
        receiver = commands.Param(converter=not_bot_member),
    ) -> None:
        """
        Добавить подарков за активность участнику
        """
        add_activity_present(inter.guild.id, receiver.id, abs(amount))
        await inter.response.send_message(
            embed = DefaultEmbed(
                title = t("give_success"),
                description = (
                    f"<@{inter.user.id}> **->** <@{receiver.id}> " +
                    f"**|** {amount} :gift:"
                )
            )
        )


class GiftsView(BaseView):
    def __init__(self, guild_id: int, user_id: int) -> None:
        super().__init__(timeout=180)
        self.guild_id = guild_id
        self.user_id = user_id
        self.gift_map = {
            t("gifts_storage_opt"): self._create_gifts_storage_embed,
            t("activity_present_opt"): self._create_activity_present_embed,
            # t("another_present"): self._create_another_present_embed
        }
        self.is_openable = False
        self.present = None
        self.add_item(GiftsSelect(self.gift_map))

    async def _response(self, inter: disnake.ApplicationCommandInteraction) -> None:
        await inter.response.send_message(
            embed=list(self.gift_map.values())[0](),
            view=self
        )

    def _build_presents_list(self) -> list[str]:
        return [
            t('activity_presents', count=get_activity_presents(
                self.guild_id, self.user_id)
            ),
            # t('another_presents')
        ]

    def _create_gifts_storage_embed(self) -> disnake.Embed:
        self.is_openable = False
        self.present = None
        return DefaultEmbed(
            title=t('gifts_storage'),
            description=self._get_storage_desc()
        )
    
    def _get_storage_desc(self) -> str:
        gifts_data = get_gifts(self.guild_id, self.user_id)
        settings = get_voice_rewards_settings(self.guild_id)
        return (ordered_list(self._build_presents_list()) + "\n\n" +
            "—"*16 + "\n" +
            t(
                'role_shards',
                shards_have=gifts_data.role if gifts_data.role < 9 else 9,
                shards_needed=settings.parts_for_role,
                role_id=settings.gifts_role
            ))
    
    def _create_activity_present_embed(self) -> disnake.Embed:
        self.is_openable = True
        self.present = PresentsMap.ACTIVITY_PRESENT
        return ActivityPresent.create_embed()

    def _create_another_present_embed(self) -> disnake.Embed:
        self.is_openable = True
        self.present = PresentsMap.ANOTHER_PRESENT
        return AnotherPresent.create_embed()


class GiftsSelect(disnake.ui.Select):
    view: GiftsView

    def __init__(self, gift_map) -> None:
        options=[
            disnake.SelectOption(
                label=name,
            ) for name in gift_map
        ]
        super().__init__(options=options)

    async def callback(
        self,
        interaction: disnake.MessageCommandInteraction,
        /
    ) -> None:
        name = self.values[0]
        self.placeholder = name
        view = self.view

        embed = view.gift_map[name]()

        view.clear_items()
        view.add_item(self)
        if view.is_openable:
            view.add_item(OpenPresent())

        await interaction.response.edit_message(
            embed=embed,
            view=view,
        )


class OpenPresent(disnake.ui.Button):
    view: GiftsView

    def __init__(self) -> None:
        super().__init__(
            style=disnake.ButtonStyle.green,
            label=t("open_present")
        )
        
    async def callback( 
            self,
            interaction: disnake.MessageCommandInteraction,
            /
        ) -> None:
        present = self.view.present
        if not present:
            return
        
        await self._process(interaction, present)

    async def _process(
            self,
            interaction: disnake.MessageCommandInteraction,
            present: PresentsMap
        ) -> None:
        await PresentsMap.get_present(present)(interaction).get_present()
        logger.info("user %d opened %s in guild %d", interaction.user.id, present.value, interaction.guild_id)


def setup(bot) -> None:
    bot.add_cog(GiftsCog(bot))