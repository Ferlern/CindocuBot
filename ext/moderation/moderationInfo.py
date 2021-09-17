from functools import update_wrapper
import re

import discord
from peewee import DoesNotExist, Query
from core import Logs
from core_elements.data_controller.models import Mod_log
from discord.ext import commands
from discord_components import Button, Interaction
from discord_components.component import Select, SelectOption
from main import SEBot
from utils.utils import DefaultEmbed, DiscordTable, TimeConstans, display_time

from ..utils.checks import is_mod
from ..utils.utils import wait_for_message
from ..utils import Interaction_inspect
from ..utils.build import page_implementation, update_message, build_page_components

INT_PATTERN = r"\d+"


class ModerationInfo(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    async def cog_check(self, ctx):
        if not ctx.guild:
            return False
        return await is_mod(self.bot.config["moderators_roles"]).predicate(ctx)

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(title="Failed to complete action",
                                  description=f"**Error**: {error}",
                                  color=0x93a5cd)
            await ctx.send(embed=embed)

    async def embed_builder(self, logs, filters):
        columns_names = ['#', 'moderator', 'action', 'target']
        columns_max_lengts = [6, 12, 6, 12]
        columns_values = []

        for log in logs:
            id = str(log['id'])
            moderator = await self.bot.get_or_fetch_member(log['moderator'])
            moderator = moderator.name
            action = log['action']

            targets = Logs.get_mod_log_targets(log['id'])
            targets_amount = len(targets)
            if targets_amount == 0:
                target = "None"
            elif targets_amount == 1:
                target = await self.bot.get_or_fetch_member(
                    targets[0]['target'])
                target = target.name
            else:
                target = f"{targets_amount} members"

            columns_values.append(
                [id, str(moderator),
                 str(action), str(target)])

        if logs:
            table = DiscordTable(columns=columns_names,
                                 max_columns_length=columns_max_lengts,
                                 values=columns_values)
        else:
            table = 'No logs found, try changing filters'

        embed = DefaultEmbed(title="All found moderation logs",
                             description=f'```\n{str(table)}```')
        if filters:
            embed.add_field(name='Sorted by:',
                            value='\n'.join([
                                f"`{key}`: {value}"
                                for key, value in filters.items()
                            ]))
            
        return embed

    def components_builder(self, filters):
        period = filters.get('period')
        action = filters.get('action')
        moderator = filters.get('moderator')
        if moderator:
            moderator_id = moderator.id
            moderator = moderator.name

        else:
            moderator_id = "None"
        actions = [
            "any", "mute", "warn", "ban", "banid", "unmute", "unwarn", "unban",
            "clear"
        ]

        components = [
            Select(id=f'moderationInfoSelectPeriod{str(period)}',
                   placeholder="select time period for search",
                   options=[
                       SelectOption(label="any", value=0),
                       SelectOption(label="1 hour",
                                    value=TimeConstans.hour,
                                    default=period == TimeConstans.hour),
                       SelectOption(label="6 hour",
                                    value=TimeConstans.six_hour,
                                    default=period == TimeConstans.six_hour),
                       SelectOption(label="1 day",
                                    value=TimeConstans.day,
                                    default=period == TimeConstans.day),
                       SelectOption(label="1 week",
                                    value=TimeConstans.week,
                                    default=period == TimeConstans.week),
                       SelectOption(label="1 month",
                                    value=TimeConstans.mounts,
                                    default=period == TimeConstans.mounts),
                   ]),
            Select(id=f'moderationInfoSelectAction{str(action)}',
                   placeholder="select action for search",
                   options=[
                       SelectOption(label=opt,
                                    value=opt,
                                    default=action == opt) for opt in actions
                   ]),
            [
                Button(style=3 if moderator else 4,
                       label='moderator',
                       id='moderationInfoModerator'),
                Button(style=1,
                       label=str(moderator),
                       disabled=True,
                       id=f'moderationInfoModerator{moderator_id}')
            ]
        ]

        return components

    async def moderation_logs_builder(self, values: dict):
        if selected := values.get('selected'):
            try:
                values["period"] = int(selected)
                if int(selected) == 0:
                    del values["period"]
            except Exception:
                values["action"] = selected
                if selected == "any":
                    del values["action"]
                    
        if moderator := values.get('moderator'):
            moderator = await self.bot.get_or_fetch_member(moderator)
            if moderator:
                values['moderator'] = moderator
            else:
                del values['moderator']
        
        filters_type = ['period', 'action', 'moderator']
        
        filters = {}
        for filter_type in filters_type:
            filter_value = values.get(filter_type)
            if filter_value: filters[filter_type] = filter_value
        
        logs_query: Query = Logs.get_mod_logs(**filters)
        
        page, last_page, logs = page_implementation(values, logs_query)
        
        page_components = build_page_components(page, last_page, 'moderationInfo')
        embed = await self.embed_builder(logs, filters)
        components = self.components_builder(filters)
        
        if page_components:
            components.insert(0, page_components)
            
        if values.get('moderator'):
            values["moderator"] = values["moderator"].id
        
        return embed, components, values

    async def select_moderator(self, interaction):
        await interaction.respond(content='Write id / name / mention for search')
        moderator = await wait_for_message(self.bot, interaction)
        
        values = Interaction_inspect.get_values(interaction)
        
        values['moderator'] = moderator
            
        embed, components, values = await self.moderation_logs_builder(values)
        components = Interaction_inspect.inject(components, values)
        await interaction.message.edit(embed=embed, components=components)
    
    @commands.Cog.listener()
    async def on_button_click(self, interaction: Interaction):
        if not Interaction_inspect.check_prefix(interaction, 'moderationInfo'): return

        component = interaction.component
        if component.label == 'moderator':
            await self.select_moderator(interaction)
            return
            
        else:
            await update_message(self.bot, self.moderation_logs_builder, interaction)

    @commands.Cog.listener()
    async def on_select_option(self, interaction: Interaction):
        if not Interaction_inspect.check_prefix(interaction, 'moderationInfo'): return
        await update_message(self.bot, self.moderation_logs_builder, interaction)

    @commands.command(aliases=['ml'])
    async def moderation_logs(self, ctx, log: int = None):
        await ctx.message.delete()
        if not log:
            values = {'page': 0}
            embed, components, values = await self.moderation_logs_builder(values)
            components = Interaction_inspect.inject(components, values)
            await ctx.send(embed=embed, components=components)
            return

        log: Mod_log = Logs.get_mod_log(id=int(log))
        if not log:
            await ctx.send(embed = DefaultEmbed(description = 'Log not found'))
            return    
        
        moderator = await self.bot.get_or_fetch_member(log.moderator)

        embed = DefaultEmbed(
            title=f"Information about action {log.id}",
            description=
            f"Moderator\n{moderator.mention} / `{moderator.name}#{moderator.discriminator}` / `{moderator.id}`\nuse command `{log.action}`\n\n<t:{log.creation_time}:f>"
        )

        embed.add_field(name="Reason", value=log.reason)

        if log.duration:
            embed.add_field(
                name="Duration",
                value=
                f"{display_time(log.duration, granularity=4, full=True)}\n <t:{log.creation_time}:f> -> <t:{log.creation_time+log.duration}:f>",
                inline=False)

        targets = Logs.get_mod_log_targets(log)
        targets = [target['target'] for target in targets]
        targets = [
            await self.bot.get_or_fetch_member(target) for target in targets
        ]

        if targets:
            embed.add_field(
                name="Targets",
                value="\n".join([
                    f"{index}. {target.mention} / `{target.name}#{target.discriminator}` / `{target.id}`"
                    for index, target in enumerate(targets, 1)
                ]),
                inline=False)

        embed.set_thumbnail(url=moderator.avatar_url)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(ModerationInfo(bot))
