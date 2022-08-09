import logging

import disnake
from core import MemberDataController
from disnake.embeds import Embed
from disnake.ext import commands
from disnake.ext.commands.errors import BadArgument
from discord_components import Button, ButtonStyle, Interaction
from main import SEBot
from utils.custom_errors import (MarriedWithAnother, NotEnoughMoney,
                                 NotMarried, TargetAlreadyMarried,
                                 UserAlreadyMarried)
from utils.utils import DefaultEmbed

from ..utils import Interaction_inspect
from ..utils.converters import InteractedMember

loger = logging.getLogger('Arctic')


class RelationshipCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot
        self.emoji = self.bot.config['additional_emoji']['relationship']

    async def cog_command_error(self, ctx, error):
        _ = ctx.get_translator()
        embed = DefaultEmbed(title=_("Can't send a marriage proposal"))
        if isinstance(error, commands.BadArgument):
            await ctx.message.delete()
            embed.description = _("**Error**: {error}").format(error=error)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.delete()
            embed.description = _("**Error**: specify member")
        else:
            embed.description = _("**Error**: unknown error")
        
        await ctx.send(embed=embed)

    async def divorce_handler(self, interaction: Interaction, author_id: int):
        _ = self.bot.get_translator_by_interaction(interaction)
        await Interaction_inspect.only_author(interaction)
        member = MemberDataController(author_id)
        target_id = member.soul_mate
        try:
            member.divorce(confirmed=True)
            member.save()
            embed = Embed(
                title=_("{emoji} Divorce").format(emoji=self.emoji['divorce']),
                description=_("couple <@{author_id}> & <@{target_id}> decides to end their relationship.").format(
                    author_id=author_id,
                    target_id=target_id,
                ),
                colour=disnake.Colour.red())
        except NotMarried:
            await interaction.respond(content=_('You are not in a relationship'))
        except MarriedWithAnother:
            await interaction.respond(content=_('This message is out of date'))
        else:
            await interaction.respond(type=7, embed=embed, components=[])

    @commands.command()
    async def marry(self, ctx, target: InteractedMember):
        loger.info(f'marry proposal from {ctx.author} to {target}')
        await ctx.message.delete()
        _ = ctx.get_translator()

        member = MemberDataController(id=ctx.author.id)
        coin = self.bot.config["coin"]
        prefix = self.bot.config["prefixes"][0]
        price = self.bot.config['marry_price']
        to_send = {}
        try:
            member.marry(target.id)
            member = MemberDataController(id=ctx.author.id)
            member.change_balance(-price)
            member.save()
        except NotEnoughMoney as e:
            embed = DefaultEmbed(
                description=_("You need {e} more {coin} to make suggestion").format(e=e, coin=coin))
        except UserAlreadyMarried:
            embed = DefaultEmbed(
                description=_("It looks like you already have a soul mate. You can use `{prefix}divorce` at any time to fix this.").format(prefix=prefix))
        except TargetAlreadyMarried:
            embed = DefaultEmbed(
                description=_("The person you want to offer to is already in a relationship"))
        else:
            embed = Embed(
                title=_("{emoji} Marriage proposal").format(emoji=self.emoji['sent']),
                description=_("{target}, {author} offer to get married, do you agree?").format(
                    target=target.mention,
                    author=ctx.author.mention,
                ),
                colour=0xffc0cb)
            components = [[
                Button(label=_('Accept'),
                       style=ButtonStyle.green,
                       id='relationshipAccept'),
                Button(label=_('Refuse'),
                       style=ButtonStyle.red,
                       id='relationshipRefuse')
            ]]
            components = Interaction_inspect.inject(components, {
                'target': target.id,
                'author': ctx.author.id
            })
            to_send['components'] = components
        to_send['embed'] = embed
        await ctx.send(**to_send)

    @commands.command()
    async def divorce(self, ctx):
        loger.debug(f'{ctx.author} call command divorce')
        await ctx.message.delete()
        _ = ctx.get_translator()

        member = MemberDataController(id=ctx.author.id)
        to_send = {}
        try:
            pair_id = member.soul_mate
            member.divorce()
            to_send['embed'] = DefaultEmbed(
                title=_("{emoji} Divorce?..").format(emoji=self.emoji['divorce']),
                description=_("Are you sure you want to end your relationship with <@{pair_id}>?").format(pair_id=pair_id),
            )
            components = [
                Button(label=_('Divorce'),
                       style=ButtonStyle.red,
                       id='relationshipDivorce')
            ]
            Interaction_inspect.inject(components, {'author': ctx.author.id})
            to_send['components'] = components
        except NotMarried:
            to_send['embed'] = DefaultEmbed(description=_('You are not in a relationship'))
        await ctx.send(**to_send)

    @commands.Cog.listener()
    async def on_button_click(self, interaction: Interaction):
        component = interaction.component
        if not component.id.startswith('relationship'):
            return
        values = Interaction_inspect.get_values(interaction)
        author_id = values.get('author')
        target_id = values.get('target')

        if component.id.startswith('relationshipDivorce'):
            await self.divorce_handler(interaction, author_id)
            return

        _ = self.bot.get_translator_by_interaction(interaction)
        if target_id != interaction.author.id:
            await interaction.respond(content=_('This offer is not for you.'))
            return

        if component.label == _('Accept'):
            member = MemberDataController(id=author_id)
            try:
                member.marry(target_id)
            except UserAlreadyMarried:
                await interaction.respond(
                    content=_('The user who sent this offer is already in a relationship')
                )
                return
            except TargetAlreadyMarried:
                await interaction.respond(content=_('You already have a soul mate'))
                return
            member.save()
            embed = Embed(
                title=_("{emoji} Offer accepted").format(emoji=self.emoji['accepted']),
                description=_("There is a new couple on this server\n<@{author_id}> & <@{target_id}>").format(
                    author_id=author_id,
                    target_id=target_id,
                ),
                colour=0x9cee90)
        elif component.label == _('Refuse'):
            embed = Embed(
                title=_("{emoji} Offer refused").format(emoji=self.emoji['refused']),
                description=_("<@{target_id}> refuse the offer. Perhaps it's time to realize your true feelings.").format(
                    target_id=target_id,
                ),
                colour=disnake.Colour.red())
        else:
            embed = DefaultEmbed(description=_('This message is out of date'))

        await interaction.respond(type=7, embed=embed, components=[])


def setup(bot):
    bot.add_cog(RelationshipCog(bot))
