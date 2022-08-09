import logging

from disnake import emoji

import core
from core import Likes, UserInfo
from disnake.ext import commands
from discord_components import Interaction
from discord_components.component import Select, SelectOption
from main import SEBot
from peewee import JOIN, fn
from utils.utils import DefaultEmbed, experience_converting, display_time

from ..utils import Interaction_inspect
from ..utils.build import update_message

loger = logging.getLogger('Arctic')


class TopCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot
        self.emoji = self.bot.config["additional_emoji"]["top"]

        config = self.bot.config
        add_emoji = config["additional_emoji"]["other"]

        _ = lambda s: s
        self.rename_dict = {
            "balance": _("balance"),
            "likes": _("reputation"),
            "married_time": _("duration of relationship"),
            "experience": _("level"),
            "voice_activity": _("voice activity"),
        }
        self.end_emoji_dict = {
            "balance": config["coin"],
            "likes": add_emoji.get('heart', ''),
            "married_time": "",
            "experience": "",
            "voice_activity": "",
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
            _ = ctx.get_translator()
            embed = DefaultEmbed(title=_("Can't complate action"),
                                 description=_("**Error**: {error}").format(error=error))
            await ctx.send(embed=embed)

    def embed_builder(self, translator, selected, items):
        _ = translator
        rename_dict = self.rename_dict
        end_emoji_dict = self.end_emoji_dict

        embed = DefaultEmbed(
            title=_("{emoji} Top by {category}").format(
                emoji=self.start_emoji_dict[selected],
                category=translator(rename_dict[selected]),
            )
        )
        
        template = "{index}. <@{item_id}> — {item_selected} {emoji}"
        if selected == 'married_time':
            template = _("{index}. <@{item_user}> & <@{item_soul_mate}> - from <t:{item_selected}:f> {emoji}")
        elif selected == 'experience':
            for item in items:
                level, gained_after_lvl_up, left_before_lvl_up = experience_converting(item[selected])
                item[selected] = f'**{level}** ({gained_after_lvl_up}/{left_before_lvl_up})'
        elif selected == 'voice_activity':
            for item in items:
                item[selected] = display_time(translator, item[selected])
                
        embed.description = (
            "\n".join([
                template.format(
                    index = index,
                    item_id = item['id'],
                    item_user = item['user'] if selected == 'married_time' else None,
                    item_soul_mate = item['soul_mate'] if selected == 'married_time' else None,
                    item_selected = item[selected],
                    emoji = end_emoji_dict[selected]
                )
                for index, item in enumerate(items, 1)
            ])
            if items else _('Empty :(')
        )
        return embed

    def build_components(self, translator, selected):
        _ = translator
        rename_dict = self.rename_dict

        return Select(id="top_select",
                      options=[
                          SelectOption(label=translator(label),
                                       value=value,
                                       default=value == selected)
                          for value, label in rename_dict.items()
                      ])

    def top_builder(self, translator, values):
        selected = values['selected']

        if selected == 'likes':
            items = (UserInfo.select(
                UserInfo.id,
                fn.COALESCE(fn.SUM(Likes.type), 0).alias('likes')).join(
                    Likes,
                    on=Likes.to_user == UserInfo.id,
                    join_type=JOIN.LEFT_OUTER).where(
                        UserInfo.on_server == True).group_by(
                            UserInfo.id).order_by(
                                fn.COALESCE(
                                    fn.SUM(Likes.type),
                                    0).desc()).limit(10).dicts().execute())
        elif selected == 'married_time':
            items = (core.Relationship.select().order_by(
                core.Relationship.married_time).limit(10).dicts().execute())
        else:
            op = getattr(UserInfo, selected)

            items = (UserInfo.select(
                UserInfo.id, op).where(UserInfo.on_server == True).order_by(
                    op.desc()).limit(10).dicts().execute())

        embed = self.embed_builder(translator, selected, items)
        components = [self.build_components(translator, selected)]

        return embed, components, values

    @commands.command()
    async def top(self, ctx):
        await ctx.message.delete()
        translator = ctx.get_translator()

        values = {
            'selected': 'voice_activity',
            'author': ctx.author.id,
            'page': 0
        }
        embed, components, values = self.top_builder(translator, values)
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
    bot.add_cog(TopCog(bot))
