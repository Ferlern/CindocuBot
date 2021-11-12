import logging

import discord
import discord_components
from core import Suggestions
from discord.errors import HTTPException
from discord.ext import commands
from discord.ext.commands.core import guild_only
from discord.ext.commands.errors import BadArgument
from discord_components.component import SelectOption
from main import SEBot
from peewee import Query
from utils.custom_errors import NotConfigured
from utils.utils import DefaultEmbed

from ..utils import Interaction_inspect
from ..utils.build import (build_page_components, page_implementation,
                           update_message)
from ..utils.checks import is_admin
from ..utils.utils import wait_message_from_author

logger = logging.getLogger('Arctic')

from discord_components import Button, ButtonStyle


class suggestions(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot
        self.emoji = self.bot.config['additional_emoji']['suggestion']

    async def suggestions_embed_builder(self, suggestion: dict):
        author = await self.bot.get_or_fetch_user(suggestion['author'])
        embed = DefaultEmbed(title=f'Suggestion',
                             description=suggestion['text'])
        embed.set_author(
            name=author.name,
            icon_url=author.avatar_url,
            url=
            f"https://discord.com/channels/{self.bot.config['guild']}/{self.bot.config['suggestions_channel']}/{suggestion['message_id']}"
        )
        if suggestion['url']:
            embed.set_image(url=suggestion['url'])
        return embed

    def suggestions_control_embed_builder(self, actual_items: dict):
        embed = DefaultEmbed(title=f"{self.emoji['list']} List of suggestions")
        if not actual_items:
            embed.description = 'There are currently no suggestions'
        else:
            for index, item in enumerate(actual_items, 1):
                embed.add_field(
                    name=f"{index}",
                    value=
                    f"From: <@{item['author']}>\n\nText (first 100): {item['text'][:100]}"
                    + (" `...`" if len(item['text']) > 100 else ""),
                    inline=False)
        return embed

    def suggestions_components_builder(self, actual_items: dict, values):
        page = values.get('page', 0)
        try:
            current = int(values.get('selected'))
        except Exception as e:
            current = None
        component = discord_components.Select(
            id='suggestions_select',
            placeholder='Select an suggestion for details',
            options=[
                SelectOption(label=str(index + 1),
                             value=page * 10 + index,
                             description=f"{item['text'][:40]}" +
                             ("..." if len(item['text']) > 40 else ""),
                             default=int(current) %
                             10 == index if current != None else False)
                for index, item in enumerate(actual_items)
            ]) if actual_items else None
        return component

    def suggestions_control_builder(self, values):
        items = Suggestions.select()
        page, last_page, actual_items = page_implementation(values, items)
        page_components = build_page_components(page, last_page, 'suggestions')

        embed = self.suggestions_control_embed_builder(actual_items)
        component = self.suggestions_components_builder(actual_items, values)
        components = [component] if component else []
        if page_components:
            components.insert(0, page_components)

        return embed, components, values

    async def suggestion_builder(self, values):
        base_id = 'suggestions_'
        items: Query = Suggestions.select()
        page, last_page, actual_items = page_implementation(values, items)
        suggestion = items.offset(int(
            values['selected'])).limit(1).dicts().execute()[0]

        embed = await self.suggestions_embed_builder(suggestion)
        component = self.suggestions_components_builder(actual_items, values)
        options = component.options
        options.insert(
            0,
            SelectOption(label='Back',
                         value='back',
                         description='To suggestion list'))
        component.set_options(options)
        components = [
            component,
            [
                Button(label='Approve',
                       style=ButtonStyle.green,
                       id=base_id + 'Approve'),
                Button(label='Deny',
                       style=ButtonStyle.red,
                       id=base_id + 'Deny'),
                Button(label='Delete',
                       style=ButtonStyle.gray,
                       id=base_id + 'Delete')
            ]
        ]
        return embed, components, values

    async def suggestion_respond(self, interaction):
        await Interaction_inspect.only_author(interaction)
        values = Interaction_inspect.get_values(interaction)

        items = Suggestions.select()
        items_amount = items.count()
        items_with_offset = items.offset(items_amount - 1)
        suggestion = items.offset(int(
            values['selected'])).limit(1).dicts().execute()[0]
        author = await self.bot.get_or_fetch_user(suggestion['author'])
        guild = self.bot.get_guild(self.bot.config['guild'])
        channel = guild.get_channel(self.bot.config['suggestions_channel'])
        try:
            message = await channel.fetch_message(suggestion['message_id'])
        except HTTPException:
            message = None

        action: str = interaction.component.label

        responded = False
        if action in ["Approve", "Deny"] and message:
            embed: discord.Embed = message.embeds[0]
            responded = True
            await interaction.respond(
                content='Write the reason, - if you have nothing to say')
            content = await wait_message_from_author(self.bot, interaction,
                                                     values['author'])
            if content in ['-', '_', "'-'", '"-"', '0']:
                content = 'Not specified'

            embed.add_field(name='suggestion' +
                            (' denied' if action == 'Deny' else ' approved'),
                            value=f'{interaction.author.mention}: {content}')
            embed.color = discord.Colour.red(
            ) if action == 'Deny' else discord.Colour.green()
            await message.edit(embed=embed)

        Suggestions.get(message_id=suggestion['message_id']).delete_instance()

        current = int(values['selected'])
        if current > items_amount - 2:
            current -= 1
        values['selected'] = str(current)

        page, last_page, elements = page_implementation(
            values, items_with_offset)
        values['page'] = page

        if items_amount > 1:
            embed, components, values = await self.suggestion_builder(values)
        else:
            embed, components, values = self.suggestions_control_builder(
                values)

        components = Interaction_inspect.inject(components, values)

        if responded:
            await interaction.message.edit(embed=embed, components=components)
        else:
            await interaction.respond(type=7,
                                      embed=embed,
                                      components=components)

    @guild_only()
    @commands.command()
    async def suggest(self, ctx, *, suggestion):
        new_lines = suggestion.count('\n')
        if new_lines > 50:
            raise BadArgument('Too many line breaks')
        elif len(suggestion) > 4000:
            raise BadArgument('Suggestion must be less than 4000 characters')
        
        await ctx.message.delete()
        try:
            url = ctx.message.attachments[0].url
        except IndexError:
            url = None
        channel = ctx.author.guild.get_channel(
            self.bot.config['suggestions_channel'])
        if not channel:
            raise NotConfigured('Channel for suggestions not specified')
        await ctx.send(embed=DefaultEmbed(
            description=f"{self.emoji['send']} Your suggestion has been sent successfully"))

        embed = DefaultEmbed(description=suggestion)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f'Member id: {ctx.author.id}')
        if url:
            embed.set_image(url=url)
        message = await channel.send(embed=embed)

        Suggestions.create(message_id=message.id,
                           text=suggestion,
                           url=url,
                           author=ctx.author.id)

    @suggest.error
    async def suggest_error(self, ctx, error):
        embed = DefaultEmbed(title="Failed to make suggestion")
        if isinstance(error, commands.BadArgument):
            await ctx.message.delete()
            embed.description = f"**Error**: {error}"
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.delete()
            embed.description = "describe your suggestion"
        await ctx.send(embed=embed)

    @is_admin()
    @commands.command(aliases=['sc'])
    async def suggestions_control(self, ctx):
        await ctx.message.delete()
        values = {
            'author': ctx.author.id,
            'page': 0,
        }
        embed, components, values = self.suggestions_control_builder(values)
        components = Interaction_inspect.inject(components, values)
        await ctx.send(embed=embed, components=components)

    @commands.Cog.listener()
    async def on_select_option(self, interaction):
        if not interaction.component.id.startswith('suggestions'):
            return

        if interaction.values[0] == 'back':
            await update_message(self.bot, self.suggestions_control_builder,
                                 interaction)
        else:
            await update_message(self.bot, self.suggestion_builder,
                                 interaction)

    @commands.Cog.listener()
    async def on_button_click(self, interaction):
        if not interaction.component.id.startswith('suggestions'):
            return

        if interaction.component.label in ["Approve", "Deny", "Delete"]:
            await self.suggestion_respond(interaction)
            return

        await update_message(self.bot, self.suggestions_control_builder,
                             interaction)


def setup(bot):
    bot.add_cog(suggestions(bot))
