import re

import discord
from core import Logs
from core_elements.data_controller.models import Mod_log
from discord.ext import commands
from discord_components import Button, Interaction
from discord_components.component import Select, SelectOption
from main import SEBot
from utils.utils import DefaultEmbed, DiscordTable, TimeConstans, display_time

from ..utils.checks import is_mod
from ..utils.utils import wait_for_message

INT_PATTERN = r"\d+"


class InteractionInspector:
    @classmethod
    def get_button_click_result(cls, interaction):
        component = interaction.component
        if isinstance(component, Button):
            return component.label if component.label else component.emoji

    @classmethod
    def get_filters(cls, interaction):
        message = interaction.message
        components = message.components

        button_with_moderator = components[3].components[1]
        select_with_period = components[1].components[0]
        select_with_action = components[2].components[0]

        filters = {}
        try:
            moderator = int(
                re.findall(INT_PATTERN, button_with_moderator.id)[0])
            filters['moderator'] = moderator
        except IndexError:
            pass
        try:
            period = int(re.findall(INT_PATTERN, select_with_period.id)[0])
            filters['period'] = int(period)
        except IndexError:
            pass
        try:
            action_id: str = select_with_action.id
            action = action_id.removeprefix("moderationInfoSelectAction")
            if action != "None":
                filters['action'] = action
        except IndexError:
            pass

        try:
            value = interaction.values[0]
            try:
                int(value)
                filters["period"] = int(value)
                if int(value) == 0:
                    del filters["period"]
            except Exception:
                filters["action"] = value
                if value == "any":
                    del filters["action"]
        except IndexError:
            pass

        return filters

    @classmethod
    def get_page(cls, interaction):
        message = interaction.message
        components = message.components

        button_with_page = components[0].components[2]
        current_page = int(re.findall(INT_PATTERN,
                                      button_with_page.label)[0]) - 1
        last_page = int(re.findall(INT_PATTERN, button_with_page.label)[1]) - 1
        if current_page > last_page:
            current_page = last_page
        return current_page, last_page


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

    async def get_actual_info(self, ctx, button_result=None):
        filters = InteractionInspector.get_filters(ctx)
        page, last_page = InteractionInspector.get_page(ctx)

        if str(button_result) in ["⏮️", "◀️", "▶️", "⏭️"]:
            if str(button_result) == "⏮️":
                page = 0
            elif str(button_result) == "◀️":
                page -= 1
                if page < 0:
                    page = last_page
            elif str(button_result) == "▶️":
                page += 1
                if page > last_page:
                    page = 0
            elif str(button_result) == "⏭️":
                page = last_page
            try:
                filters['moderator'] = await self.bot.get_or_fetch_member(
                    filters['moderator'])
            except KeyError:
                pass

        else:
            if isinstance(button_result, discord.User):
                filters['moderator'] = button_result
            elif isinstance(button_result, str):
                try:
                    del filters['moderator']
                except KeyError:
                    pass
            else:
                try:
                    filters['moderator'] = await self.bot.get_or_fetch_member(
                        filters['moderator'])
                except KeyError:
                    pass

        return filters, page

    async def build_actual_components(self, page, **filters):
        def get_last_page(logs):
            page = (len(logs) - 1) // 10
            return page if page >= 0 else 0

        def cut_logs(logs, page):
            if not len(logs):
                return

            expected_last_page = get_last_page(logs)
            cut = logs[page * 10:(page + 1) * 10]

            if not cut:
                cut = cut_logs(logs, expected_last_page)

            return cut

        logs = Logs.get_mod_logs(**filters)

        last_page = get_last_page(logs)
        if page > last_page:
            page = last_page

        actual_log = cut_logs(logs, page)
        if not actual_log:
            actual_log = []

        columns_names = ['#', 'moderator', 'action', 'target']
        columns_max_lengts = [6, 12, 6, 12]
        columns_values = []

        for log in actual_log:
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
            [
                Button(emoji=str("⏮️"), id='moderationInfotrack_previous'),
                Button(emoji=str("◀️"), id='moderationInfoarrow_backward'),
                Button(label=f"({page+1}/{last_page+1})",
                       disabled=True,
                       id='moderationInfo'),
                Button(emoji=str("▶️"), id='moderationInfoarrow_forward'),
                Button(emoji=str("⏭️"), id='moderationInfotrack_next'),
            ],
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

        return embed, components

    @commands.Cog.listener()
    async def on_button_click(self, ctx: Interaction):
        component = ctx.component
        id: str = component.id
        if not id.startswith("moderationInfo"):
            return

        if component.label == 'moderator':
            await ctx.respond(content='Write id / name / mention for search')
            moderator = await wait_for_message(self.bot, ctx)
            new_moderator = await self.bot.get_or_fetch_member(moderator)
            button_result = new_moderator if new_moderator else moderator
        else:
            button_result = InteractionInspector.get_button_click_result(ctx)
            await ctx.respond(type=7)

        filters, page = await self.get_actual_info(ctx, button_result)

        embed, components = await self.build_actual_components(page, **filters)

        await ctx.message.edit(embed=embed, components=components)

    @commands.Cog.listener()
    async def on_select_option(self, ctx: Interaction):
        component = ctx.component
        id: str = component.id
        if not id.startswith("moderationInfo"):
            return

        filters, page = await self.get_actual_info(ctx)

        embed, components = await self.build_actual_components(page, **filters)

        await ctx.respond(type=7, embed=embed, components=components)

    @commands.command(aliases=['ml'])
    async def moderation_logs(self, ctx, log: int = None):
        await ctx.message.delete()
        if not log:
            embed, components = await self.build_actual_components(0)
            await ctx.send(embed=embed, components=components)
            return

        log: Mod_log = Logs.get_mod_log(id=int(log))
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
