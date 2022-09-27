from typing import Optional, Union

import disnake
from disnake.ext import commands

from src.custom_errors import BadConfigured, UsedNotOnGuild
from src.database.models import Suggestions
from src.discord_views.base_view import BaseView
from src.discord_views.embeds import DefaultEmbed
from src.utils.slash_shortcuts import only_guild, only_admin
from src.translation import get_translator
from src.logger import get_logger
from src.discord_views.paginate.peewee_paginator import (PeeweePaginator,
                                                         PeeweeItemSelect)
from src.ext.suggestions.services import (get_suggestion_settings,
                                          create_suggestion)
from src.bot import SEBot


logger = get_logger()
t = get_translator(route="ext.suggestions")


class SuggestionsCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    @commands.slash_command(**only_guild)
    async def suggest(
        self,
        inter: disnake.ApplicationCommandInteraction,
        text: str,
        attachment: Optional[disnake.Attachment] = None,
    ) -> None:
        """
        Опубликовать предложение для сервера

        Parameters
        ----------
        text: Текст вашего предложения
        attachment: Скриншот/видео/гиф изображение
        """
        guild = inter.guild
        if not guild:
            raise UsedNotOnGuild

        settings = get_suggestion_settings(guild.id)
        channel = guild.get_channel(
            settings.suggestions_channel)  # type: ignore

        if not channel or not isinstance(channel, disnake.TextChannel):
            raise BadConfigured(t('no_suggestion_channel'))

        await inter.response.send_message(embed=DefaultEmbed(
            description=t('suggestion_sended'),
        ))
        author = inter.author
        embed = DefaultEmbed(description=text)
        embed.set_author(
            name=author.name,
            icon_url=await self.bot.save_avatar(author)
        )
        embed.set_footer(text=t('suggestion_footer', author_id=author.id))
        if attachment:
            file = await attachment.to_file()
            embed.set_image(file=file)
        message = await channel.send(embed=embed)

        attachment_url = message.embeds[0].image.url or None

        create_suggestion(
            author.id,
            message_id=message.id,
            guild_id=guild.id,
            channel_id=channel.id,
            text=text,
            url=attachment_url,  # type: ignore
        )
        logger.info(
            'new suggestion on guild %d from user %d',
            guild.id,
            author.id,
        )

    @commands.slash_command(**only_admin)
    async def suggestions_control(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ) -> None:
        """
        Управлять предложениями на этом сервере
        """
        logger.debug(
            'suggestion control called for %d', inter.author.id,
        )
        paginator = SuggestionPaginator(inter.guild)  # type: ignore
        await paginator.start_from(inter)


class SuggestionPaginator(PeeweePaginator):
    def __init__(self, guild: disnake.Guild) -> None:
        super().__init__(
            Suggestions,
            items_per_page=5,
            filters={'guild': Suggestions.guild_id == guild.id},
        )
        self.add_paginator_item(SuggestionSelect())

    async def page_callback(self,
                            interaction: Union[disnake.ModalInteraction,
                                               disnake.MessageInteraction]
                            ) -> None:
        await interaction.response.edit_message(
            embed=self.create_embed(),
            view=self,
        )

    async def continue_from(
        self,
        inter: Union[disnake.MessageInteraction, disnake.ModalInteraction],
    ) -> None:
        self.update()
        await inter.response.edit_message(
            embed=self.create_embed(),
            view=self if not self.is_empty() else None,
        )
        logger.debug('SuggestionPaginator continue from %s', inter)

    def create_embed(self) -> disnake.Embed:
        items_repr = [t(
            'select_item_desc',
            index=idx,
            author_id=item.author,
            text=item.text,
        ) for idx, item in enumerate(self.items, 1)]

        embed = DefaultEmbed(
            title=t('list_title'),
            description="\n\n".join(items_repr) or t('empty_list'),
        )
        return embed

    async def _response(self, inter: disnake.ApplicationCommandInteraction):
        to_send = {}
        to_send['embed'] = self.create_embed()
        if not self.is_empty():
            to_send['view'] = self
        await inter.response.send_message(
            **to_send,
        )


class SuggestionSelect(PeeweeItemSelect[Suggestions]):
    view: SuggestionPaginator

    def __init__(self) -> None:
        super().__init__(t('select_for_datails'))

    async def _resolve_select(
        self,
        inter: disnake.MessageInteraction,
        item: Suggestions,
    ) -> None:
        await SuggestionManager.continue_from(
            inter=inter,
            suggestion=item,
            suggestions_paginator=self.view,
        )

    def _build_option_description(
        self,
        _: int,
        item: Suggestions
    ) -> str:
        text = item.text
        return text[:40] + '...' if len(text) > 40 else text  # type: ignore


class SuggestionManager(BaseView):
    def __init__(  # noqa
        self,
        bot: SEBot,
        author: disnake.Member,
        message: disnake.Message,
        suggestion: Suggestions,
        suggestions_paginator: SuggestionPaginator,
    ) -> None:
        super().__init__()
        self.bot = bot
        self.author = author
        self.message = message
        self._suggestion = suggestion
        self._suggestions_paginator = suggestions_paginator
        self._suggestion_author = None

    @classmethod
    async def continue_from(
        cls,
        inter: disnake.MessageInteraction,
        suggestion: Suggestions,
        suggestions_paginator: SuggestionPaginator,
    ):
        logger.debug('SuggestionManager continue from %s', inter)
        instance = cls(
            inter.bot,  # type: ignore
            inter.author,  # type: ignore
            inter.message,
            suggestion,
            suggestions_paginator=suggestions_paginator,
        )
        await inter.response.edit_message(
            embed=await instance.create_embed(),
            view=instance,
        )

    async def create_embed(self) -> disnake.Embed:
        suggestion = self._suggestion

        author = await self.bot.get_or_fetch_user(
            suggestion.author,  # type: ignore
        )
        self._suggestion_author = author
        embed = DefaultEmbed(
            title=t('suggestion'),
            description=suggestion.text,
        )
        if author:
            embed.set_author(
                name=author.display_name,
                icon_url=author.display_avatar.url,
                url=f"https://discord.com/channels/{suggestion.guild_id}/"
                    f"{suggestion.channel_id}/{suggestion.message_id}"
            )
        if suggestion.url:
            embed.set_image(url=suggestion.url)
        return embed

    @disnake.ui.button(
        label=t('button_accept_label'),
        style=disnake.ButtonStyle.green,
    )
    async def accept(
        self,
        _: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        logger.debug('SuggestionManager accept clicked by %d',
                     interaction.author.id)
        await self._resolve_action(
            interaction,
            action_label=t('response_approved'),
            action_color=disnake.Colour.green().value,
        )

    @disnake.ui.button(
        label=t('button_reject_label'),
        style=disnake.ButtonStyle.red,
    )
    async def reject(
        self,
        _: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        logger.debug('SuggestionManager reject clicked by %d',
                     interaction.author.id)
        await self._resolve_action(
            interaction,
            action_label=t('response_rejected'),
            action_color=disnake.Colour.red().value,
        )

    @disnake.ui.button(
        label=t('button_delete_label'),
        style=disnake.ButtonStyle.gray,
    )
    async def delete(
        self,
        _: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        logger.debug('SuggestionManager delete clicked by %d',
                     interaction.author.id)
        self._suggestion.delete_instance()
        await self._suggestions_paginator.continue_from(interaction)

    @disnake.ui.button(
        label=t('button_back_label'),
        style=disnake.ButtonStyle.gray,
    )
    async def back(
        self,
        _: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        logger.debug('SuggestionManager back clicked by %d',
                     interaction.author.id)
        await self._suggestions_paginator.continue_from(interaction)

    async def _resolve_action(
        self,
        inter: disnake.MessageInteraction,
        action_label: str,
        action_color: int,
    ):
        suggestion = self._suggestion
        guild = self.author.guild
        channel = guild.get_channel(
            suggestion.channel_id,  # type: ignore
        )
        if (not channel or
                not isinstance(channel, disnake.TextChannel)):
            await inter.response.send_message(
                t('resnonse_cant_find'),
                ephemeral=True,
            )
            return

        try:
            message = await channel.fetch_message(
                suggestion.message_id,  # type: ignore
            )
        except disnake.errors.NotFound:
            await inter.response.send_message(
                t('resnonse_cant_find'),
                ephemeral=True,
            )
            return
        embed = message.embeds[0]

        async def callback(
            reason: str,
        ) -> None:
            embed.add_field(
                name=f"{t('suggestion')} {action_label}",
                value=f'{inter.author.mention}: {reason}',
            )
            embed.color = action_color
            self._suggestion.delete_instance()
            # attachments=[] really needed. But yeah idk why.
            await message.edit(embed=embed, attachments=[])
            logger.info(
                "suggestion on guild %d resolved by %d",
                guild.id,
                inter.author.id,
            )

        logger.debug('creating SuggestionModal for %d', inter.author.id)
        await inter.response.send_modal(SuggestionModal(
            self._suggestions_paginator,
            callback,
        ))


class SuggestionModal(disnake.ui.Modal):
    def __init__(
        self,
        backref: SuggestionPaginator,
        edit_callback,
    ) -> None:
        components = [
            disnake.ui.TextInput(
                label=t('modal_reason'),
                custom_id="reason",
                style=disnake.TextInputStyle.long,
                value=t('modal_no_reason'),
                required=True,
                max_length=1024,
            ),
        ]
        super().__init__(
            title=t('modal_reason'),
            components=components,
        )
        self._backref = backref
        self._edit_callback = edit_callback

    async def callback(
        self,
        interaction: disnake.ModalInteraction,
        /,
    ) -> None:
        reason = interaction.text_values['reason']
        await self._edit_callback(reason)
        await self._backref.continue_from(interaction)


def setup(bot):
    bot.add_cog(SuggestionsCog(bot))
