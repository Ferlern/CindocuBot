import json
import logging

import discord_components
from disnake.ext import commands
from discord_components.component import Select, SelectOption
from main import SEBot
from utils.utils import DefaultEmbed

from ..utils import Interaction_inspect
from ..utils.build import update_message
from ..utils.checks import is_owner
from ..utils.utils import wait_message_from_author

logger = logging.getLogger('Arctic')

from discord_components import Interaction


class ConfigCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot
        self.data = bot.config

    async def cog_check(self, ctx):
        return await is_owner().predicate(ctx)

    def config_builder(self, translator, values):
        _ = translator
        selected = values.get('selected', None)
        if selected == 'all':
            selected = None

        if not selected:
            embed = DefaultEmbed(title=_('Config'),
                                 description='\n'.join([
                                     f'{key} — `{value}`'
                                     for key, value in self.data.items()
                                 ]))
        else:
            embed = DefaultEmbed(
                title=selected,
                description=
                f'```json\n{json.dumps(self.data[selected], indent=4, ensure_ascii=False)}\n```')
            embed.add_field(name=_('expected (current) type'),
                            value=str(type(self.data[selected])))

        options = [SelectOption(label=_('all'), value='all')]
        options.extend([
            SelectOption(label=key, value=key, default=selected == key)
            for key in self.data.keys()
        ])

        components = [Select(id='config_select', options=options)]
        if selected:
            components.append(
                discord_components.Button(label=_('Change'), id='config_change'))

        return embed, components, values

    async def change_value(self, interaction: Interaction):
        translator = self.bot.get_translator_by_interaction(interaction)
        _ = translator
        values = Interaction_inspect.get_values(interaction)
        selected = values['selected']

        await interaction.respond(content=_('Write new value'))
        new_value: str = await wait_message_from_author(self.bot, interaction,
                                                   values['author'])
        
        new_value = new_value.strip('```\n')

        expected = type(self.data[selected])
        try:
            new_value = json.loads(new_value)
            assert type(new_value) == expected, _('type should not change')
        except Exception as e:
            await interaction.channel.send(embed=DefaultEmbed(
                title=_('Wrong value type'), description=_('**Error**: {error}').format(error=e)))
            return

        self.data[selected] = new_value
        self.bot.reload_config()
        self.data = self.bot.config

        embed, components, values = self.config_builder(translator, values)
        components = Interaction_inspect.inject(components, values)

        await interaction.message.edit(embed=embed, components=components)

    @commands.command()
    async def config(self, ctx):
        await ctx.message.delete()
        translator = ctx.get_translator()

        values = {'author': ctx.message.author.id}
        embed, components, values = self.config_builder(translator, values)

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
    bot.add_cog(ConfigCog(bot))
