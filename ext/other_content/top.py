import logging

import core
from core import Likes, User_info
from discord.ext import commands
from discord_components import Interaction
from discord_components.component import Select, SelectOption
from main import SEBot
from peewee import JOIN, fn
from utils.utils import DefaultEmbed

from ..utils import Interaction_inspect
from ..utils.build import update_message

loger = logging.getLogger('Arctic')


class Top(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot
        self.emoji = self.bot.config["additional_emoji"]["top"]

        config = self.bot.config
        add_emoji = config["additional_emoji"]

        self.rename_dict = {
            "balance": "balance",
            "likes": "reputation",
            "married_time": "duration of relationship",
            "experience": "level",
            "voice_activity": "voice activity"
        }
        self.end_emoji_dict = {
            "balance": config["coin"],
            "likes": add_emoji.get('heart', ''),
            "married_time": "",
            "experience": "",
            "voice_activity": ""
        }
        self.start_emoji_dict = {
            "balance": self.emoji["balance"],
            "likes": self.emoji["reputation"],
            "married_time": self.emoji["soul_mate"],
            "experience": self.emoji["level"],
            "voice_activity": self.emoji["voice"]
        }

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = DefaultEmbed(title="Сan't set biography",
                                 description=f"**Error**: {error}")
            await ctx.send(embed=embed)

    def embed_builder(self, selected, items):
        rename_dict = self.rename_dict
        end_emoji_dict = self.end_emoji_dict

        if selected == 'married_time':
            embed = DefaultEmbed(
                title=f"{self.start_emoji_dict[selected]} Top by {rename_dict[selected]}",
                description=("\n".join([
                    f"{index}. <@{item['user']}> & <@{item['soul_mate']}> — from <t:{item[selected]}:f> {end_emoji_dict[selected]}"
                    for index, item in enumerate(items, 1)
                ])) if items else 'Empty :(')
        else:
            embed = DefaultEmbed(
                title=f"{self.start_emoji_dict[selected]} Top by {rename_dict[selected]}",
                description=("\n".join([
                    f"{index}. <@{item['id']}> — {item[selected]} {end_emoji_dict[selected]}"
                    for index, item in enumerate(items, 1)
                ])) if items else 'Empty :(')
        return embed

    def build_components(self, selected):
        rename_dict = self.rename_dict

        return Select(id="top_select",
                      options=[
                          SelectOption(label=label,
                                       value=value,
                                       default=value == selected)
                          for value, label in rename_dict.items()
                      ])

    def top_builder(self, values):
        selected = values['selected']

        if selected == 'likes':
            items = (User_info.select(
                User_info.id,
                fn.COALESCE(fn.SUM(Likes.type), 0).alias('likes')).join(
                    Likes,
                    on=Likes.to_user == User_info.id,
                    join_type=JOIN.LEFT_OUTER).where(
                        User_info.on_server == True).group_by(
                            User_info.id).order_by(
                                fn.COALESCE(
                                    fn.SUM(Likes.type),
                                    0).desc()).limit(10).dicts().execute())
        elif selected == 'married_time':
            items = (core.Relationship.select().order_by(
                core.Relationship.married_time).limit(10).dicts().execute())
        else:
            op = getattr(User_info, selected)

            items = (User_info.select(
                User_info.id, op).where(User_info.on_server == True).order_by(
                    op.desc()).limit(10).dicts().execute())

        embed = self.embed_builder(selected, items)
        components = [self.build_components(selected)]

        return embed, components, values

    @commands.command()
    async def top(self, ctx):
        await ctx.message.delete()
        values = {
            'selected': 'voice_activity',
            'author': ctx.author.id,
            'page': 0
        }
        embed, components, values = self.top_builder(values)
        components = Interaction_inspect.inject(components, values)
        await ctx.send(embed=embed, components=components)

    @commands.Cog.listener()
    async def on_button_click(self, interaction: Interaction):
        if not Interaction_inspect.check_prefix(interaction, 'top'):
            return
        await update_message(self.bot, self.top_builder, interaction)

    @commands.Cog.listener()
    async def on_select_option(self, interaction: Interaction):
        if not Interaction_inspect.check_prefix(interaction, 'top'):
            return
        await update_message(self.bot, self.top_builder, interaction)


def setup(bot):
    bot.add_cog(Top(bot))
