from typing import Optional, Union

import disnake
from disnake.ext import commands

from src.database.models import PremoderationItem
from src.utils.slash_shortcuts import only_admin
from src.translation import get_translator
from src.logger import get_logger
from src.discord_views.paginate.peewee_paginator import (PeeweePaginator)
from src.discord_views.paginate.paginators import PaginationItem
from src.ext.premoderation.services import (get_premoderation_settings,
                                            create_premoderation_item,
                                            delete_items_by_author)
from src.formatters import to_mention_and_id
from src.bot import SEBot


logger = get_logger()
t = get_translator(route="ext.premoderation")


class PremoderationCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        guild = message.guild
        if not guild or message.author.bot:
            return

        settings = get_premoderation_settings(guild.id)
        premoderation_channels = settings.premoderation_channels
        channel = message.channel

        if not premoderation_channels:
            return

        if channel.id not in premoderation_channels:  # type: ignore
            return

        urls = []
        for attachment in message.attachments:
            content_type = attachment.content_type
            if not content_type:
                continue
            if not (content_type.startswith('image') or content_type.startswith('video')):  # noqa
                continue

            saved_url = await self.bot.save_file(await attachment.to_file())
            if not saved_url:
                logger.warning('Premoderation work skipped, '
                               'no channels to save images')
                return
            urls.append(saved_url)
        content = message.clean_content

        await message.delete()

        if not urls and not content:
            await channel.send(t('no_content'), delete_after=5)
            return

        await channel.send(t('content_found'), delete_after=5)
        create_premoderation_item(
            guild.id, message.author.id,
            content=content,
            channel_id=channel.id,
            urls=urls,
        )

    @commands.slash_command(**only_admin)
    async def premoderation(
        self,
        inter: disnake.GuildCommandInteraction,
    ) -> None:
        """
        Управлять премодерацией на этом сервере
        """
        logger.debug(
            'premoderation called for %d', inter.author.id,
        )
        paginator = PremoderationPaginator(inter.guild)
        await paginator.start_from(inter)


class PremoderationPaginator(PeeweePaginator[PremoderationItem]):
    def __init__(self, guild: disnake.Guild) -> None:
        self.guild = guild
        super().__init__(
            PremoderationItem,
            items_per_page=1,
            filters={'guild': PremoderationItem.guild_id == guild.id},
        )
        self.add_paginator_item(PostButton())
        self.add_item(RejectButton())
        self.add_item(RejectAuthoredButton())

    async def page_callback(self,
                            interaction: Union[disnake.ModalInteraction,
                                               disnake.MessageInteraction]
                            ) -> None:
        if self.is_empty():
            await interaction.response.edit_message(
                content=t('no_premoderation_items'),
                embed=None,
                view=None,
            )
            self.stop()
            return

        await interaction.response.edit_message(
            content=self.create_message(),
            view=self,
            allowed_mentions=disnake.AllowedMentions(users=False),
        )

    @property
    def item(self) -> PremoderationItem:
        return self.items[0]

    @property
    def channel(self) -> Optional[disnake.TextChannel]:
        if self.is_empty():
            return None

        channel = self.guild.get_channel(self.item.channel_id)  # type: ignore
        if isinstance(channel, disnake.TextChannel):
            return channel
        return None

    def delete_all_from_current_author(self):
        delete_items_by_author(
            guild_id=self.guild.id,
            user_id=self.item.author,  # type: ignore
        )

    def create_message(self) -> str:
        message = str()
        backslash = '\n'
        item = self.item
        message += f"{t('from_user')}: {to_mention_and_id(item.author.id)}"  # type: ignore
        message += f"\n{t('to_channel')}: {to_mention_and_id(item.channel_id, '#')}"  # type: ignore
        if item.content:
            message += f"\n{(t('content'))}: {item.content}"
        if item.urls:
            message += f"\n\n{(t('files'))}: {backslash.join([str(url) for url in item.urls])}"
        return message

    async def _response(self, inter: disnake.ApplicationCommandInteraction):
        if self.is_empty():
            await inter.response.send_message(t('no_premoderation_items'),
                                              ephemeral=True)
            return

        await inter.response.send_message(
            content=self.create_message(),
            view=self,
            allowed_mentions=disnake.AllowedMentions(users=False),
        )


class PostButton(disnake.ui.Button, PaginationItem):
    view: PremoderationPaginator

    def __init__(self) -> None:
        super().__init__(
            style=disnake.ButtonStyle.green,
            label=t('post_button_label'),
        )

    def update(self):
        self.disabled = self.view.channel is None

    async def callback(
        self,
        interaction: disnake.MessageInteraction,
        /,
    ) -> None:
        item = self.view.item
        is_exist = item.delete_instance()
        channel = self.view.channel

        self.view.update_page()
        self.view.update()

        await self.view.resolve_interaction(interaction)

        if is_exist:
            content = f"**{t('from_user')}**: <@{item.author.id}>"
            if item.content:
                content += f"\n\n{item.content}"
            message = await channel.send(  # type: ignore
                content=content,
                allowed_mentions=disnake.AllowedMentions(users=False),
            )
            for url in item.urls:
                message = await channel.send(  # type: ignore
                    content=url,
                )
            await message.add_reaction('❤️')
            await message.add_reaction('💔')


class RejectButton(disnake.ui.Button):
    view: PremoderationPaginator

    def __init__(self) -> None:
        super().__init__(
            style=disnake.ButtonStyle.red,
            label=t('reject_button_label'),
        )

    async def callback(
        self,
        interaction: disnake.MessageInteraction,
        /,
    ) -> None:
        self.view.item.delete_instance()

        self.view.update_page()
        self.view.update()

        await self.view.resolve_interaction(interaction)


class RejectAuthoredButton(disnake.ui.Button):
    view: PremoderationPaginator

    def __init__(self) -> None:
        super().__init__(
            style=disnake.ButtonStyle.red,
            label=t('reject_all_button_label'),
        )

    async def callback(
        self,
        interaction: disnake.MessageInteraction,
        /,
    ) -> None:
        self.view.delete_all_from_current_author()

        self.view.update_page()
        self.view.update()

        await self.view.resolve_interaction(interaction)


def setup(bot):
    bot.add_cog(PremoderationCog(bot))
