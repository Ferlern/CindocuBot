import logging
from typing import Optional

import disnake
from disnake.ext import commands

from src.custom_errors import (UserAlreadyInRelationship,
                               TargetAlreadyInRelationship,
                               UsedNotOnGuild)
from src.discord_views.embeds import DefaultEmbed
from src.discord_views.base_view import BaseView
from src.converters import interacted_member
from src.utils.color import EmbedColors
from src.utils.slash_shortcuts import only_guild
from src.ext.relationship.services import (get_user_relationships_or_none,
                                           get_relationships_settings,
                                           create_relationships)
from src.ext.economy.services import change_balance
from src.translation import get_translator
from src.bot import SEBot


loger = logging.getLogger('Arctic')
t = get_translator(route="ext.relationships")


class RelationshipCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    @commands.slash_command(**only_guild)
    async def marry(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member=commands.Param(converter=interacted_member),
    ):
        """
        Предложить другому участнику стать парой

        Parameters
        ----------
        member: Участник, которому будет отправлено предложение
        """
        view = RelationshipProposalView(
            inter.author,  # type: ignore
            member,
        )
        await view.start_from(inter)

    @commands.slash_command(**only_guild)
    async def divorce(self, inter: disnake.ApplicationCommandInteraction):
        """
        Закончить свои отношения
        """
        divorce_view = DivorceView(inter.author)  # type: ignore
        await divorce_view.start_from(inter)


class RelationshipProposalView(BaseView):
    def __init__(
        self,
        author: disnake.Member,
        target: disnake.Member,
        *,
        timeout: Optional[float] = 300,
    ) -> None:
        super().__init__(timeout=timeout)
        self.author = author
        self._target = target
        self._price = get_relationships_settings(author.guild.id).marry_price

    async def _response(self, inter: disnake.ApplicationCommandInteraction):
        guild = inter.guild
        if not guild:
            raise UsedNotOnGuild

        guild_id = guild.id
        author_id = inter.author.id
        target_id = self._target.id

        self._check_relationships()
        change_balance(
            guild_id=guild_id,
            user_id=author_id,
            amount=-self._price,  # type: ignore
        )
        await inter.response.send_message(
            embed=disnake.Embed(
                title=t('relationships_proposal_title'),
                description=t(
                    'relationships_proposal_desc',
                    author_id=author_id,
                    target_id=target_id,
                ),
                colour=EmbedColors.RELATIONSHIPS,
            ),
            view=self,
        )

    @disnake.ui.button(
        label=t('accept_button_label'),
        style=disnake.ButtonStyle.green,
    )
    async def accept(
        self,
        _: disnake.ui.Button,
        interaction: disnake.MessageInteraction
    ) -> None:
        guild_id = self.author.guild.id
        author_id = self.author.id
        target_id = self._target.id

        self._check_relationships()
        create_relationships(
            guild_id,
            author_id,
            target_id
        )
        await interaction.response.edit_message(
            embed=disnake.Embed(
                title=t('accepted_title'),
                description=t(
                    'accepted_desc',
                    author_id=author_id,
                    target_id=target_id,
                ),
                color=EmbedColors.RELATIONSHIPS_ACCEPT,
            ),
            view=None,
        )
        self.stop()

    @disnake.ui.button(
        label=t('refuse_button_label'),
        style=disnake.ButtonStyle.red,
    )
    async def refuse(
        self,
        _: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        guild_id = self.author.guild.id
        author_id = self.author.id
        target_id = self._target.id
        change_balance(
            guild_id=guild_id,
            user_id=author_id,
            amount=self._price  # type: ignore
        )
        await interaction.response.edit_message(
            embed=disnake.Embed(
                title=t('refused_title'),
                description=t(
                    'refused_desc',
                    target_id=target_id,
                ),
                color=EmbedColors.RELATIONSHIPS_REFUSE,
            ),
            view=None
        )
        self.stop()

    async def on_timeout(self) -> None:
        guild_id = self.author.guild.id
        author_id = self.author.id
        target_id = self._target.id
        change_balance(
            guild_id=guild_id,
            user_id=author_id,
            amount=self._price  # type: ignore
        )
        await self.message.edit(
            embed=disnake.Embed(
                title=t('timeout_title'),
                description=t(
                    'timeout_desc',
                    target_id=target_id,
                )
            ),
            view=None,
        )

    async def interaction_check(
        self,
        interaction: disnake.MessageInteraction
    ) -> bool:
        if interaction.author.id == self._target.id:
            return True

        await interaction.response.send_message(
            t('not_for_you'),
            ephemeral=True,
        )
        return False

    def _check_relationships(self) -> None:
        guild_id = self.author.guild.id
        author_id = self.author.id
        target_id = self._target.id

        if get_user_relationships_or_none(
            guild_id=guild_id,
            user_id=author_id,
        ):
            raise UserAlreadyInRelationship(
                t('user_already_in_relationships'),
            )
        if get_user_relationships_or_none(
            guild_id=guild_id,
            user_id=target_id,
        ):
            raise TargetAlreadyInRelationship(
                t('target_already_in_relationships'),
            )


class DivorceView(BaseView):
    def __init__(
        self,
        author: disnake.Member,
        *,
        timeout: Optional[float] = 300
    ) -> None:
        super().__init__(timeout=timeout)
        self.author = author

    async def _response(self, inter: disnake.ApplicationCommandInteraction):
        guild_id = self.author.guild.id
        author_id = self.author.id

        if not get_user_relationships_or_none(
            guild_id=guild_id,
            user_id=author_id,
        ):
            await inter.response.send_message(
                embed=DefaultEmbed(
                    title=t('no_relationship'),
                ),
                ephemeral=True
            )
            self.stop()
            return

        await inter.response.send_message(
            embed=DefaultEmbed(
                title=t('divorce_confirm_title'),
                description=t('divorce_confirm_desc'),
            ),
            view=self,
        )

    @disnake.ui.button(
        label=t('divorce_button_label'),
        style=disnake.ButtonStyle.red,
    )
    async def divorce(
        self,
        _: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        guild_id = self.author.guild.id
        author_id = self.author.id

        relationship = get_user_relationships_or_none(
            guild_id=guild_id,
            user_id=author_id,
        )
        if not relationship:
            await interaction.response.edit_message(
                embed=DefaultEmbed(
                    title=t('no_relationship'),
                ),
                view=None,
            )
            return

        relationship.delete_instance()
        await interaction.response.edit_message(
            embed=disnake.Embed(
                title=t('divorce_succes_title'),
                description=t(
                    'divorce_succes_desc',
                    author_id=author_id,
                ),
            ),
            view=None,
        )


def setup(bot):
    bot.add_cog(RelationshipCog(bot))
