import logging

import discord
from core import MemberDataController, PersonalVoice, UserRoles
from discord.ext import commands
from discord.utils import get
from main import SEBot
from utils.utils import DefaultEmbed

from ..utils.checks import is_owner

logger = logging.getLogger('Arctic')
added = set[int]
outdated = set[int]


class SyncCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot
        self.in_recovery = []

    def get_roles_change(self,
                         target: discord.Member) -> tuple[outdated, added]:
        member_info = MemberDataController(target.id)

        user_roles_ids = [
            role.id for role in target.roles if role.name != '@everyone'
        ]
        saved_roles = member_info.user_info.user_roles
        saved_roles_ids = [role.role_id for role in saved_roles]

        added = set(user_roles_ids) - set(saved_roles_ids)
        outdated = set(saved_roles_ids) - set(user_roles_ids)

        return outdated, added

    def update_saved_roles(self, target: discord.Member):
        if target in self.in_recovery:
            return

        outdated, added = self.get_roles_change(target)
        logger.debug(
            f'update_saved_roles called for member {target}:\noutdated{outdated}\nadded{added}'
        )

        for role in added:
            UserRoles.get_or_create(user=target.id, role_id=role)
        for role in outdated:
            role_in_db: UserRoles = UserRoles.get_or_none(user=target.id,
                                                            role_id=role)
            if role_in_db: role_in_db.delete_instance()

    async def recovery_member_roles(self, target: discord.Member):
        self.in_recovery.append(target)

        outdated, added = self.get_roles_change(target)
        logger.debug(
            f'recovery_membet_roles called for member {target}:\noutdated{outdated}\nadded{added}'
        )

        outdated = [target.guild.get_role(role) for role in outdated]
        added = [target.guild.get_role(role) for role in added]

        await target.add_roles(*outdated, reason='Recovery')
        await target.remove_roles(*added, reason='Recovery')

        self.in_recovery.remove(target)

    async def recovery_member_voice(self, target: discord.Member):
        guild: discord.Guild = target.guild
        member_info = MemberDataController(target.id)

        voice: PersonalVoice = member_info.user_info.user_personal_voice
        if len(voice) == 0: return
        voice = voice[0]
        if not guild.get_channel(voice.voice_id):
            logger.debug(f'Recovery personal voice channel for {target.name}')
            category = get(guild.categories,
                           id=self.bot.config['personal_voice']['categoty'])
            new_voice = await guild.create_voice_channel(
                name=target.name, category=category, user_limit=voice.slots
            )
            await new_voice.set_permissions(
                            target,
                            manage_permissions = True,
                            manage_channels = True
                        )
            voice.voice_id = new_voice.id
            voice.save()

    async def sync_user(self, target: discord.Member):
        logger.debug(f'sync {target.name}')
        
        cog = self.bot.get_cog('VoiceActivityCog')
        cog.external_sync(target)
        
        await self.recovery_member_roles(target)
        await self.recovery_member_voice(target)

    def save_guild_info(self, guild: discord.Guild):
        logger.debug(f'save_guild_info for guild {guild.name}')
        members = guild.members
        for member in members:
            self.update_saved_roles(member)

    @commands.command()
    async def sync(self, ctx, target: discord.Member = None):
        if not target: target = ctx.author
        
        try:
            await self.sync_user(target)
        except Exception as e:
            logger.exception('Failed to sync user')
            await ctx.tick(False)
        else:
            await ctx.tick(True)

    @is_owner()
    @commands.command()
    async def init(self, ctx):
        _ = ctx.get_translator()
        embed = DefaultEmbed(description =
            _('This action will overwrite the data for this guild.')\
            + _('Do not use if you are not sure you know the result.')
        )
        message = await ctx.confirm(embed=embed)
        await message.delete()
        try:
            self.save_guild_info(ctx.guild)
        except Exception as e:
            logger.exception('Failed to save guild data')
            await ctx.tick(False)
        else:
            await ctx.tick(True)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member,
                               after: discord.Member):
        if before.roles != after.roles and len(after.roles) > 0:
            self.update_saved_roles(after)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.recovery_member_roles(member)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.save_guild_info(guild)


def setup(bot):
    bot.add_cog(SyncCog(bot))
