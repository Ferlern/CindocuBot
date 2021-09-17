import logging

import discord
from core import User_roles
from discord.ext import commands
from main import SEBot

logger = logging.getLogger('Arctic')


class Role_recovery(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member,
                               after: discord.Member):
        to_save = set(after.roles) - set(before.roles)
        to_remove = set(before.roles) - set(after.roles)

        for role in to_save:
            logger.debug(f'add role {role} to {after.name}')
            User_roles.get_or_create(user=after.id, role_id=role.id)
        for role in to_remove:
            logger.debug(f'remove role {role} from {after.name}')
            role_in_db: User_roles = User_roles.get_or_none(user=after.id,
                                                            role_id=role.id)
            if role_in_db: role_in_db.delete_instance()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        saved_roles = User_roles.select(User_roles.role_id).where(
            User_roles.user == member.id).dicts().execute()
        saved_roles_ids = [role['role_id'] for role in saved_roles]
        to_add = [
            member.guild.get_role(role_id) for role_id in saved_roles_ids
            if member.guild.get_role(role_id)
        ]
        logger.debug(f'recovery roles {to_add} for {member.name}')
        await member.add_roles(*to_add, reason='Recovery')


def setup(bot):
    bot.add_cog(Role_recovery(bot))
