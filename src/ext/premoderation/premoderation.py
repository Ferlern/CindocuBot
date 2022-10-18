from typing import Optional, Union
import re

import disnake
from disnake.ext import commands

from src.database.models import PremoderationItem
from src.discord_views.embeds import DefaultEmbed
from src.utils.slash_shortcuts import only_admin
from src.translation import get_translator
from src.logger import get_logger
from src.discord_views.paginate.peewee_paginator import (PeeweePaginator)
from src.discord_views.paginate.paginators import PaginationItem
from src.ext.premoderation.services import (get_premoderation_settings,
                                            create_premoderation_items,
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

        content_urls = re.findall(r'https?:\/\/\S*', message.content)
        checked_content_urls = [url for url in content_urls
                                if await self.bot.possible_embed_image(url)]
        urls.extend(checked_content_urls)

        await message.delete()

        if not urls:
            await channel.send(t('no_content'), delete_after=5)
            return

        await channel.send(t('content_found', count=len(urls)),
                           delete_after=5)
        create_premoderation_items(
            guild.id, message.author.id,
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
            return

        await interaction.response.edit_message(
            embed=self.create_embed(),
            view=self,
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

    def create_embed(self) -> disnake.Embed:
        embed = DefaultEmbed()
        item = self.item
        embed.add_field(
            name=t('from_user'),
            value=to_mention_and_id(item.author),  # type: ignore
            inline=False,
        )
        embed.add_field(
            name=t('to_channel'),
            value=to_mention_and_id(item.channel_id, '#'),  # type: ignore
        )
        embed.add_field(
            name=t('url'),
            value=str(item.url),
        )
        embed.set_image(item.url)
        embed.set_footer(text=t('premoderation_embed_footer'))
        return embed

    async def _response(self, inter: disnake.ApplicationCommandInteraction):
        if self.is_empty():
            await inter.response.send_message(t('no_premoderation_items'),
                                              ephemeral=True)
            return

        await inter.response.send_message(
            embed=self.create_embed(),
            view=self,
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

        if is_exist:
            channel = self.view.channel
            embed = DefaultEmbed(description=f'{t("from_user")} <@{item.author.id}>')
            embed.set_image(item.url)
            message = await channel.send(  # type: ignore
                embed=embed,
            )
            await message.add_reaction('❤️')
            await message.add_reaction('💔')

        self.view.update_page()
        self.view.update()

        await self.view.resolve_interaction(interaction)


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
