import logging

import discord
from core import Member_data_controller
from discord.embeds import Embed
from discord.ext import commands
from discord.ext.commands.errors import BadArgument
from discord_components import Button, ButtonStyle, Interaction
from main import SEBot
from utils.custom_errors import (MarriedWithAnother, NotEnoughMoney,
                                 NotMarried, TargetAlreadyMarried,
                                 UserAlreadyMarried)
from utils.utils import DefaultEmbed

from ..utils import Interaction_inspect

loger = logging.getLogger('Arctic')


class relationship(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot
        self.emoji = self.bot.config['additional_emoji']['relationship']

    async def cog_command_error(self, ctx, error):
        embed = DefaultEmbed(title="Сan't send a marriage proposal")
        if isinstance(error, commands.BadArgument):
            embed.description = f"**Error**: {error}"
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.delete()
            embed.description = f"**Error**: specify member"
        
        await ctx.send(embed=embed)

    async def divorce_handler(self, interaction: Interaction, author_id: int):
        await Interaction_inspect.only_author(interaction)
        member = Member_data_controller(author_id)
        target_id = member.soul_mate
        try:
            member.divorce(confirmed=True)
            member.save()
            embed = Embed(
                title=f"{self.emoji['divorce']} Divorce",
                description=
                f"couple <@{author_id}> & <@{target_id}> decides to end their relationship.",
                colour=discord.Colour.red())
        except NotMarried:
            await interaction.respond(content='You are not in a relationship')
        except MarriedWithAnother:
            await interaction.respond(content='This message is out of date')
        else:
            await interaction.respond(type=7, embed=embed, components=[])

    @commands.command()
    async def marry(self, ctx, target: discord.Member):
        loger.info(f'marry proposal from {ctx.author} to {target}')
        await ctx.message.delete()

        if ctx.author == target:
            raise BadArgument('The specified user must not be ... you')
        if target.bot:
            raise BadArgument('The specified user must not be a bot')

        member = Member_data_controller(id=ctx.author.id)
        coin = self.bot.config["coin"]
        prefix = self.bot.config["prefixes"][0]
        price = self.bot.config['marry_price']
        to_send = {}
        try:
            member.marry(target.id)
            member = Member_data_controller(id=ctx.author.id)
            member.change_balance(-price)
            member.save()
        except NotEnoughMoney as e:
            embed = DefaultEmbed(
                description=f"You need {e} more {coin} to make suggestion")
        except UserAlreadyMarried:
            embed = DefaultEmbed(
                description=
                f"It looks like you already have a soul mate. You can use `{prefix}divorce` at any time to fix this."
            )
        except TargetAlreadyMarried:
            embed = DefaultEmbed(
                description=
                f"The person you want to offer to is already in a relationship"
            )
        else:
            embed = Embed(
                title=f"{self.emoji['sent']} Marriage proposal",
                description=
                f"{target.mention}, {ctx.author.mention} offer to get married, do you agree?",
                colour=0xffc0cb)
            components = [[
                Button(label='Accept',
                       style=ButtonStyle.green,
                       id='relationshipAccept'),
                Button(label='Refuse',
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
        await ctx.message.delete()
        loger.debug(f'{ctx.author} call command divorce')
        member = Member_data_controller(id=ctx.author.id)
        to_send = {}
        try:
            pair_id = member.soul_mate
            member.divorce()
            to_send['embed'] = DefaultEmbed(
                title=f"{self.emoji['divorce']} Divorce?..",
                description=
                f"Are you sure you want to end your relationship with <@{pair_id}>?"
            )
            components = [
                Button(label=f'Divorce',
                       style=ButtonStyle.red,
                       id='relationshipDivorce')
            ]
            Interaction_inspect.inject(components, {'author': ctx.author.id})
            to_send['components'] = components
        except NotMarried:
            to_send['embed'] = DefaultEmbed(
                description='You are not in a relationship')
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

        if target_id != interaction.author.id:
            await interaction.respond(content='This offer is not for you.')
            return

        if component.label == 'Accept':
            member = Member_data_controller(id=author_id)
            try:
                member.marry(target_id)
            except UserAlreadyMarried:
                await interaction.respond(
                    content=
                    'The user who sent this offer is already in a relationship'
                )
                return
            except TargetAlreadyMarried:
                await interaction.respond(
                    content='You already have a soul mate')
                return
            member.save()
            embed = Embed(
                title=f"{self.emoji['accepted']} Offer accepted",
                description=
                f"There is a new couple on this server\n<@{author_id}> & <@{target_id}>",
                colour=0x9cee90)
        elif component.label == 'Refuse':
            embed = Embed(
                title=f"{self.emoji['refused']} Offer refused",
                description=
                f"<@{target_id}> refuse the offer. Perhaps it's time to realize your true feelings.",
                colour=discord.Colour.red())

        await interaction.respond(type=7, embed=embed, components=[])


def setup(bot):
    bot.add_cog(relationship(bot))
