from functools import update_wrapper
import re

import discord
from peewee import DoesNotExist, Query
from core import Logs
from core_elements.data_controller.models import ModLog
from discord.ext import commands
from discord_components import Button, Interaction
from discord_components.component import Select, SelectOption
from main import SEBot
from utils.utils import DefaultEmbed, DiscordTable, TimeConstants, display_time

from ..utils.checks import is_mod
from ..utils.utils import wait_for_message
from ..utils import Interaction_inspect
from ..utils.build import page_implementation, update_message, build_page_components

INT_PATTERN = r"\d+"


class ModerationInfoCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot
        self.emoji = self.bot.config["additional_emoji"]["other"]

    async def cog_check(self, ctx):
        if not ctx.guild:
            return False
        return await is_mod().predicate(ctx)

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            _ = ctx.get_translator()
            embed = discord.Embed(title=_("Failed to complete action"),
                                  description=_("**Error**: {error}").format(error=error),
                                  color=0x93a5cd)
            await ctx.send(embed=embed)

    async def embed_builder(self, translator, logs, filters):
        _ = translator
        columns_names = ['#', 'moderator', 'action', 'target']
        columns_max_lengts = [6, 12, 6, 12]
        columns_values = []

        for log in logs:
            id = str(log['id'])
            moderator = await self.bot.get_or_fetch_user(log['moderator'])
            moderator = moderator.name
            action = log['action']

            targets = Logs.get_mod_log_targets(log['id'])
            targets_amount = len(targets)
            if targets_amount == 0:
                target = "None"
            elif targets_amount == 1:
                target = await self.bot.get_or_fetch_user(
                    targets[0]['target'])
                target = target.name
            else:
                target = _("{targets_amount} members").format(targets_amount=targets_amount)

            columns_values.append(
                [id, str(moderator),
                 str(action), str(target)])

        if logs:
            table = DiscordTable(columns=columns_names,
                                 max_columns_length=columns_max_lengts,
                                 values=columns_values)
        else:
            table = _('No logs found, try changing filters')

        embed = DefaultEmbed(title=_("{emoji} All found moderation logs").format(emoji=self.emoji['all_mod_log']),
                             description=f'```\n{str(table)}```')
        if filters:
            embed.add_field(name=_('Sorted by:'),
                            value='\n'.join([
                                f"`{key}`: {value}"
                                for key, value in filters.items()
                            ]))
            
        return embed

    def components_builder(self, translator, filters):
        _ = translator
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
                   placeholder=_("select time period for search"),
                   options=[
                       SelectOption(label=_("any"), value=0),
                       SelectOption(label=_("1 hour"),
                                    value=TimeConstants.hour,
                                    default=period == TimeConstants.hour),
                       SelectOption(label=_("6 hour"),
                                    value=TimeConstants.six_hour,
                                    default=period == TimeConstants.six_hour),
                       SelectOption(label=_("1 day"),
                                    value=TimeConstants.day,
                                    default=period == TimeConstants.day),
                       SelectOption(label=_("1 week"),
                                    value=TimeConstants.week,
                                    default=period == TimeConstants.week),
                       SelectOption(label=_("1 month"),
                                    value=TimeConstants.mounts,
                                    default=period == TimeConstants.mounts),
                   ]),
            Select(id=f'moderationInfoSelectAction{str(action)}',
                   placeholder=_("select action for search"),
                   options=[
                       SelectOption(label=opt,
                                    value=opt,
                                    default=action == opt) for opt in actions
                   ]),
            [
                Button(style=3 if moderator else 4,
                       label=_('moderator'),
                       id='moderationInfoModerator'),
                Button(style=1,
                       label=str(moderator),
                       disabled=True,
                       id=f'moderationInfoModerator{moderator_id}')
            ]
        ]

        return components

    async def moderation_logs_builder(self, translator, values: dict):
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
            moderator = await self.bot.get_or_fetch_user(moderator)
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
        embed = await self.embed_builder(translator, logs, filters)
        components = self.components_builder(translator, filters)
        
        if page_components:
            components.insert(0, page_components)
            
        if values.get('moderator'):
            values["moderator"] = values["moderator"].id
        
        return embed, components, values

    async def select_moderator(self, interaction):
        translator = self.bot.get_translator_by_interaction(interaction)
        _ = translator
        await interaction.respond(content=_('Write id / name / mention for search'))
        moderator = await wait_for_message(self.bot, interaction)
        
        values = Interaction_inspect.get_values(interaction)
        
        values['moderator'] = moderator
            
        embed, components, values = await self.moderation_logs_builder(translator, values)
        components = Interaction_inspect.inject(components, values)
        await interaction.message.edit(embed=embed, components=components)
    
    @commands.Cog.listener()
    async def on_button_click(self, interaction: Interaction):
        if not Interaction_inspect.check_prefix(interaction, 'moderationInfo'): return

        _ = self.bot.get_translator_by_interaction(interaction)
        component = interaction.component
        if component.label == _('moderator'):
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
        translator = ctx.get_translator()
        _ = translator

        if not log:
            values = {'page': 0}
            embed, components, values = await self.moderation_logs_builder(translator, values)
            components = Interaction_inspect.inject(components, values)
            await ctx.send(embed=embed, components=components)
            return

        log: ModLog = Logs.get_mod_log(id=int(log))
        if not log:
            await ctx.send(embed = DefaultEmbed(description = _('Log not found')))
            return    
        
        moderator = await self.bot.get_or_fetch_user(log.moderator)

        embed = DefaultEmbed(
            title=_("Information about action {id}").format(id=log.id),
            description=
            _("Moderator\n{mention} / `{name}#{discriminator}` / `{id}`\nuse command `{action}`\n\n<t:{creation_time}:f>").format(
                mention=moderator.mention,
                name=moderator.name,
                discriminator=moderator.discriminator,
                id=moderator.id,
                action=log.action,
                creation_time=log.creation_time,
            )
        )

        embed.add_field(name=_("Reason"), value=log.reason)

        if log.duration:
            embed.add_field(
                name=_("Duration"),
                value=
                f"{display_time(translator, log.duration, granularity=4, full=True)}\n <t:{log.creation_time}:f> -> <t:{log.creation_time+log.duration}:f>",
                inline=False)

        targets = Logs.get_mod_log_targets(log)
        targets = [target['target'] for target in targets]
        targets = [
            await self.bot.get_or_fetch_user(target) for target in targets
        ]

        if targets:
            embed.add_field(
                name=_("Targets"),
                value="\n".join([
                    f"{index}. {target.mention} / `{target.name}#{target.discriminator}` / `{target.id}`"
                    for index, target in enumerate(targets, 1)
                ]),
                inline=False)

        embed.set_thumbnail(url=moderator.avatar_url)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(ModerationInfoCog(bot))
