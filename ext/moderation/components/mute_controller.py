import asyncio
import logging
import time

import core
import discord
from discord.ext import commands, tasks
from main import SEBot

logger = logging.getLogger('Arctic')


class Mute_controller:
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot

    def cancel(self):
        self.mute_controller.cancel()

    def start(self):
        self.mute_controller.start()

    @tasks.loop(hours=1)
    async def mute_controller(self):
        logger.info('mute_controller called')
        try:
            model = core.Member_data_controller.model
            query = model.select().where(
                model.mute_end_at <= time.time() + 3600)
            muted_members = query.dicts().execute()

            for member in muted_members:
                d_member = self.bot.get_guild_member(member["id"])
                if not d_member:
                    logger.warning(
                        f"Can't find user {member['id']}. Maybe, he leave the server"
                    )
                    continue
                time_to_end = member["mute_end_at"] - time.time()
                time_to_end = 0 if time_to_end < 0 else time_to_end

                await self.clean_mute(d_member, time_to_end)
        except Exception as e:
            logger.exception('mute_controller caused an error')

    async def clean_mute(self, member: discord.Member, mute_time: int = 0):
        """Checks if the mute time has expired, removes the role, removes the entry from the database

        Args:
            member (discord.Member)
            mute_time (int, optional): mute duration (in seconds). Defaults to 0.
        """
        logger.debug(f'clean_mute ready for {member}. time: {mute_time}')
        await asyncio.sleep(mute_time + 1)
        member_info = core.Member_data_controller(member.id)
        role = discord.utils.get(member.guild.roles,
                                 id=self.bot.config["mute_role"])
        if member_info.user_info.mute_end_at:
            if not role or member_info.user_info.mute_end_at > time.time():
                return
        try:
            await member.remove_roles(role, reason="mute time expired")
        except:
            pass
        finally:
            member_info.end_mute()
            member_info.save()

    async def mute_members(self, ctx, members, time, reason):
        role = discord.utils.get(members[0].guild.roles,
                                 id=self.bot.config["mute_role"])
        if not role:
            raise commands.BadArgument("mute role not specified. Check config")
        muted = []
        for member in members:
            try:
                await member.add_roles(role, reason=reason)
                member_info = core.Member_data_controller(member.id)
                muted.append(member)
                member_info.set_mute_time(time)
                member_info.save()
                if time <= 3600:
                    asyncio.ensure_future(self.clean_mute(member, time))
            except Exception as e:
                pass
        return muted
