import asyncio
from typing import Optional, Union
import aiohttp
import io

import disnake
from disnake.ext import commands

from src.custom_errors import RegularException
from src.database.models import CreatedShopRoles, PremoderationItem
from src.utils.custom_ids import CREATE_ROLE_COLOR, CREATE_ROLE_NAME
from src.utils.slash_shortcuts import only_admin
from src.translation import get_translator
from src.logger import get_logger
from src.discord_views.paginate.peewee_paginator import PeeweePaginator
from src.discord_views.paginate.paginators import PaginationItem
from src.discord_views.switch import ViewSwitcher
from src.ext.economy.services import add_role_to_inventory
from src.ext.economy.services import CurrencyType, change_balance, get_economy_settings
from src.ext.premoderation.services import (get_premoderation_settings,
                                            create_premoderation_item,
                                            delete_items_by_author)
from src.formatters import to_mention_and_id
from src.bot import SEBot


logger = get_logger()
t = get_translator(route="ext.premoderation")


class PremoderationCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
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
            logger.debug('Premoderatnio: new content, type: %s', content_type)
            if not content_type:
                continue
            if not content_type.startswith(('image', 'video', 'audio')):
                continue

            saved_url = await self.bot.save_file(await attachment.to_file())
            if not saved_url:
                continue
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
        switcher = PremoderationSwitcher()
        switcher.add_view(
            PremoderationPaginator(self.bot, inter.guild), label=t('content_premoderation')
        )
        switcher.add_view(RolePremoderationPaginator(inter.guild), label=t('roles_premoderation'))
        await switcher.start_from(inter)


class PremoderationPaginator(PeeweePaginator[PremoderationItem]):
    def __init__(self, bot: SEBot, guild: disnake.Guild) -> None:
        self.guild = guild
        self._bot = bot
        super().__init__(
            PremoderationItem,
            items_per_page=1,
            filters={'guild': PremoderationItem.guild_id == guild.id},
        )
        self.add_paginator_item(PostButton())
        self.add_paginator_item(RejectButton())
        self.add_paginator_item(RejectAuthoredButton())

    async def page_callback(
        self,
        interaction: Union[disnake.ModalInteraction, disnake.MessageInteraction],
    ) -> None:
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

        channel = self.guild.get_channel(self.item.channel_id)
        if isinstance(channel, disnake.TextChannel):
            return channel

    def create_message(self) -> str:
        if self.is_empty():
            return t('no_premoderation_items')
        message = str()
        backslash = '\n'
        item = self.item
        message += f"{t('from_user')}: {to_mention_and_id(item.author.id)}"
        message += f"\n{t('to_channel')}: {to_mention_and_id(item.channel_id, '#')}"
        if item.content:
            message += f"\n{(t('content'))}: {item.content}"
        if item.urls:
            message += f"\n\n{(t('files'))}: {backslash.join([str(url) for url in item.urls])}"
        return message

    async def _response(self, inter: disnake.ApplicationCommandInteraction) -> None:
        await inter.response.send_message(
            content=self.create_message(),
            view=self,
            allowed_mentions=disnake.AllowedMentions(users=False),
        )

    def delete_all_from_current_author(self) -> None:
        delete_items_by_author(
            guild_id=self.guild.id,
            user_id=self.item.author,  # type: ignore
        )

    def can_accept(self) -> bool:
        return self.channel is not None

    def reject(self) -> None:
        self.item.delete_instance()

    async def accept(self) -> None:
        item = self.item
        exists = item.delete_instance()
        channel = self.channel

        if not exists:
            return

        asyncio.create_task(_send_item(self._bot, self.item, channel))  # type: ignore


async def _send_item(bot: SEBot, item: PremoderationItem, channel: disnake.TextChannel) -> None:
    content = f"**{t('from_user')}**: <@{item.author.id}>"
    if item.content:
        content += f"\n\n{item.content}"
    async with bot.lock(channel):
        message = await channel.send(
            content=content,
            allowed_mentions=disnake.AllowedMentions(users=False),
        )
        if item.urls is not None:
            for url in item.urls:
                if _is_audio_file(url):
                    message = await _download_and_send(channel, url) or message
                else:
                    message = await channel.send(
                        content=url,
                    )
        await message.add_reaction('❤️')
        await message.add_reaction('💔')


async def _download_and_send(channel: disnake.TextChannel, url: str) -> Optional[disnake.Message]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status != 200:
                return

            *_, filename = url.split('/')
            payload = io.BytesIO(await r.read())
            file = disnake.File(fp=payload, filename=filename or 'file.mp3')
            return await channel.send(file=file)


def _is_audio_file(url: str) -> bool:
    return url.endswith(('mp3', 'wav', 'aiff', 'ape', 'flac', 'ogg'))


class RolePremoderationPaginator(PeeweePaginator[CreatedShopRoles]):
    def __init__(self, guild: disnake.Guild) -> None:
        self.guild = guild
        self._settings = get_economy_settings(guild.id)
        super().__init__(
            CreatedShopRoles,
            items_per_page=1,
            filters={
                'guild': CreatedShopRoles.guild == guild.id,
                'approved': CreatedShopRoles.approved == False,  # type: ignore # noqa
            },
        )
        self.add_paginator_item(PostButton())
        self.add_paginator_item(RejectButton())

    async def page_callback(
        self,
        interaction: Union[disnake.ModalInteraction, disnake.MessageInteraction],
    ) -> None:
        await interaction.response.edit_message(
            content=self.create_message(),
            view=self,
            allowed_mentions=disnake.AllowedMentions(users=False),
        )

    @property
    def item(self) -> CreatedShopRoles:
        return self.items[0]

    def create_message(self) -> str:
        if self.is_empty():
            return t('no_premoderation_items')
        item = self.item
        message = f"{t('from_user')}: {to_mention_and_id(item.creator.id)}\n\n"
        message += f"{t('role_color')}: {str(item.properties[CREATE_ROLE_COLOR])}\n"
        message += f"{t('role_name')}: {str(item.properties[CREATE_ROLE_NAME])}"

        return message

    async def _response(self, inter: disnake.ApplicationCommandInteraction) -> None:
        await inter.response.send_message(
            content=self.create_message(),
            view=self,
            allowed_mentions=disnake.AllowedMentions(users=False),
        )

    def can_accept(self) -> bool:
        return not self.is_empty()

    def reject(self) -> None:
        item = self.item
        exist = self.item.delete_instance()
        if not exist:
            return
        change_balance(
            item.guild.id,
            item.creator.id,
            self._settings.role_creation_price,
            currency=CurrencyType.CRYSTAL,
        )

    async def accept(self) -> None:
        item = self.item
        guild = self.guild
        item.approved = True
        try:
            role = await guild.create_role(
                color=int(f'0x{item.properties[CREATE_ROLE_COLOR].lstrip("#")}', 16),
                name=item.properties[CREATE_ROLE_NAME],
            )
        except (disnake.HTTPException, ValueError) as error:
            raise RegularException(t('invalid_role')) from error
        under_role = guild.get_role(self._settings.role_under_which_create_roles)  # type: ignore
        if under_role:
            await role.edit(position=under_role.position - 1)
        add_role_to_inventory(item.guild.id, item.creator.id, role.id, item.price)
        item.role_id = role.id
        item.save()


class PostButton(disnake.ui.Button, PaginationItem):
    view: PremoderationPaginator

    def __init__(self) -> None:
        super().__init__(
            style=disnake.ButtonStyle.green,
            label=t('post_button_label'),
        )

    def update(self) -> None:
        self.disabled = not self.view.can_accept()

    async def callback(
        self,
        interaction: disnake.MessageInteraction,
        /,
    ) -> None:
        await self.view.accept()
        self.view.update()
        await self.view.resolve_interaction(interaction)


class RejectButton(disnake.ui.Button, PaginationItem):
    view: PremoderationPaginator

    def __init__(self) -> None:
        super().__init__(
            style=disnake.ButtonStyle.red,
            label=t('reject_button_label'),
        )

    def update(self) -> None:
        self.disabled = self.view.is_empty()

    async def callback(
        self,
        interaction: disnake.MessageInteraction,
        /,
    ) -> None:
        self.view.reject()

        self.view.update()

        await self.view.resolve_interaction(interaction)


class RejectAuthoredButton(disnake.ui.Button, PaginationItem):
    view: PremoderationPaginator

    def __init__(self) -> None:
        super().__init__(
            style=disnake.ButtonStyle.red,
            label=t('reject_all_button_label'),
        )

    def update(self) -> None:
        self.disabled = self.view.is_empty()

    async def callback(
        self,
        interaction: disnake.MessageInteraction,
        /,
    ) -> None:
        self.view.delete_all_from_current_author()
        self.view.update()
        await self.view.resolve_interaction(interaction)


class PremoderationSwitcher(ViewSwitcher):
    async def _resolve_selection(
        self, view, inter: disnake.MessageInteraction,
    ) -> None:
        await inter.response.edit_message(
            view.create_message(),  # type: ignore
            view=view,
            allowed_mentions=disnake.AllowedMentions(users=False),
        )


def setup(bot) -> None:
    bot.add_cog(PremoderationCog(bot))
