import json
import logging

import discord_components
from discord.ext import commands
from discord_components.component import Select, SelectOption
from main import SEBot
from utils.utils import DefaultEmbed

from ..utils import Interaction_inspect
from ..utils.build import update_message
from ..utils.checks import is_owner
from ..utils.utils import wait_message_from_author

logger = logging.getLogger('Arctic')

from discord_components import Interaction


class Config(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot
        self.data = bot.config

    async def cog_check(self, ctx):
        return await is_owner().predicate(ctx)

    def config_builder(self, values):
        selected = values.get('selected', None)
        if selected == 'all':
            selected = None

        if not selected:
            embed = DefaultEmbed(title='config',
                                 description='\n'.join([
                                     f'{key} — `{value}`'
                                     for key, value in self.data.items()
                                 ]))
        else:
            embed = DefaultEmbed(
                title=selected,
                description=
                f'```json\n{json.dumps(self.data[selected], indent=4)}```')
            embed.add_field(name='expected (current) type',
                            value=str(type(self.data[selected])))

        options = [SelectOption(label='all', value='all')]
        options.extend([
            SelectOption(label=key, value=key, default=selected == key)
            for key in self.data.keys()
        ])
        print(len(options), options)

        components = [Select(id='config_select', options=options)]
        if selected:
            components.append(
                discord_components.Button(label='Change', id='config_change'))

        return embed, components, values

    async def change_value(self, interaction: Interaction):
        values = Interaction_inspect.get_values(interaction)
        selected = values['selected']

        await interaction.respond(content='Write new value')
        new_value = await wait_message_from_author(self.bot, interaction,
                                                   values['author'])

        expected = type(self.data[selected])
        try:
            new_value = json.loads(new_value)
            print(type(new_value), '?', expected)
            assert type(new_value) == expected, 'type should not change'
        except Exception as e:
            await interaction.channel.send(embed=DefaultEmbed(
                title='Wrong value type', description=f'**Error**: {e}'))
            return

        self.data[selected] = new_value
        self.bot.configurator.reload()

        embed, components, values = self.config_builder(values)
        components = Interaction_inspect.inject(components, values)

        await interaction.message.edit(embed=embed, components=components)

    @commands.command()
    async def config(self, ctx):
        await ctx.message.delete()

        values = {'author': ctx.message.author.id}
        embed, components, values = self.config_builder(values)

        components = Interaction_inspect.inject(components, values)
        await ctx.send(embed=embed, components=components)

    @commands.Cog.listener()
    async def on_button_click(self, interaction: Interaction):
        if not Interaction_inspect.check_prefix(interaction, 'config'):
            return

        await Interaction_inspect.only_author(interaction)
        await self.change_value(interaction)

    @commands.Cog.listener()
    async def on_select_option(self, interaction: Interaction):
        if not Interaction_inspect.check_prefix(interaction, 'config'):
            return

        await update_message(self.bot, self.config_builder, interaction)


def setup(bot):
    bot.add_cog(Config(bot))
