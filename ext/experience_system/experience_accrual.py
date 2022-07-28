import asyncio
import random

import discord
from core import MemberDataController
from discord.ext import commands
from main import SEBot
from utils.utils import DefaultEmbed


class ExperienceAccrualCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot
        self.on_cooldown = []

    def add_exp(self, author, config):
        member = MemberDataController(id=author.id)
        old_level = member.level[0]
        member.user_info.experience += random.randint(
            config['experience_per_message'][0],
            config['experience_per_message'][1])
        member.save()
        new_level = member.level[0]
        self.on_cooldown.append(author)
        return old_level, new_level

    def add_coins(self, new_level, author, config):
        member = MemberDataController(id=author.id)
        member.change_balance(100 + new_level*config['coins_per_level_up'])
        member.save()

    def get_roles(self, author, new_level, config):
        levels_with_role = list(config['roles'].keys())
        if str(new_level) in levels_with_role:
            old_role_index = levels_with_role.index(str(new_level)) - 1

            role_id = config['roles'][str(new_level)]

            old_role_lvl = levels_with_role[old_role_index]
            old_role_id = config['roles'][old_role_lvl]

            guild: discord.Guild = author.guild

            new_role = guild.get_role(role_id)
            if old_role_index >= 0:
                old_role = guild.get_role(old_role_id)
            else:
                old_role = None
            return old_role, new_role
        else:
            return None, None

    def embed_builder(self, author, new_role, old_level, new_level, config, translator):
        _ = translator
        embed = DefaultEmbed(
            description=_('{author} got a level up ({old_level} -> {new_level})').format(
                author=author.mention,
                old_level=old_level,
                new_level=new_level,
            ))

        value = f"{100 + new_level*config['coins_per_level_up']} {self.bot.config['coin']}"
        if new_role:
            value += _("\nRole <@&{role_id}>").format(role_id=new_role.id)

        embed.add_field(name=_('Bonuses'), value=value)
        return embed

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        translator = self.bot.get_translator_by_guild(message.guild)
        _ = translator
        config = self.bot.config['experience_system']
        author: discord.Member = message.author

        checks = (message.channel.id in config['experience_channels'], author
                  not in self.on_cooldown, not author.bot,
                  len(message.content) >= config['minimal_message_length'])

        if all(checks):
            old_level, new_level = self.add_exp(author, config)

            if new_level - old_level > 0:
                self.add_coins(new_level, author, config)
                old_role, new_role = self.get_roles(author, new_level, config)

                if new_role:
                    await author.add_roles(new_role,
                                           reason=_('Level {new_level} reached').format(new_level=new_level))
                if old_role:
                    await author.remove_roles(
                        old_role,
                        reason=_('Level {new_level} reached, remove old role').format(new_level=new_level))

                embed = self.embed_builder(author, new_role, old_level,
                                           new_level, config, translator)
                await message.channel.send(embed=embed, delete_after=30)

            await asyncio.sleep(config['cooldown'])
            self.on_cooldown.remove(author)


def setup(bot):
    bot.add_cog(ExperienceAccrualCog(bot))
