import logging
import sys
import traceback

import discord
from core import Personal_voice, User_info, User_roles
from discord.ext import commands
from discord.utils import get
from main import SEBot

logger = logging.getLogger('Arctic')


class Sync(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    async def sync_user(self, target: discord.Member, start=False):
        logger.debug(f'sync {target.name}')
        guild: discord.Guild = target.guild
        member_info = User_info(target.id)
        saved_roles = User_roles.select(User_roles.role_id).where(
            User_roles.user == target.id).dicts().execute()

        user_roles_ids = [
            role.id for role in target.roles if role.name != '@everyone'
        ]
        saved_roles_ids = [role['role_id'] for role in saved_roles]

        to_save = set(user_roles_ids) - set(saved_roles_ids)
        to_remove = set(saved_roles_ids) - set(user_roles_ids)

        if start:
            for role in to_save:
                User_roles.get_or_create(user=target.id, role_id=role.id)
            for role in to_remove:
                role_in_db: User_roles = User_roles.get_or_none(
                    user=target.id, role_id=role.id)
                if role_in_db: role_in_db.delete_instance()

        else:
            to_add = [
                guild.get_role(role_id) for role_id in to_remove
                if guild.get_role(role_id)
            ]
            to_remove = [
                guild.get_role(role_id) for role_id in to_save
                if guild.get_role(role_id)
            ]

            await target.add_roles(*to_add, reason='Recovery')
            await target.remove_roles(*to_remove, reason='Recovery')

        voice: Personal_voice = member_info.user_personal_voice
        if not voice: return
        if not guild.get_channel(voice['voice_id']):
            category = get(guild.categories,
                           id=self.bot.config['personal_voice']['categoty'])
            await guild.create_voice_channel(name=target.name,
                                             category=category,
                                             user_limit=voice['slots'])

    @commands.command()
    async def sync(self, ctx):
        try:
            await self.sync_user(ctx.author)
        except Exception as e:
            logger.exception('Failed to sync user')
            await ctx.tick(False)
        else:
            await ctx.tick(True)


def setup(bot):
    bot.add_cog(Sync(bot))
