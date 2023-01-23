import disnake
from disnake.ext import commands

from src.logger import get_logger
from src.ext.members.services import get_member_roles, create_member_roles, delete_member_roles
from src.utils.roles import filter_assignable
from src.bot import SEBot


logger = get_logger()


Outdated = set[int]
Added = set[int]


class RoleControllerCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot
        self.in_recovery = []

    def get_roles_changes(
        self,
        target: disnake.Member,
    ) -> tuple[Outdated, Added]:
        saved_roles = get_member_roles(
            target.guild.id,
            target.id
        )
        member_data_roles_ids = {item.role_id for item in saved_roles}  # noqa
        member_roles_ids = {role.id for role in target.roles if role.name != '@everyone'}

        added = member_roles_ids - member_data_roles_ids
        outdated = member_data_roles_ids - member_roles_ids

        return outdated, added

    def update_saved_roles(self, target: disnake.Member) -> None:
        if target in self.in_recovery:
            return

        guild_id = target.guild.id
        user_id = target.id
        outdated, added = self.get_roles_changes(target)
        create_member_roles(guild_id, user_id, list(added))
        delete_member_roles(guild_id, user_id, list(outdated))

    async def recovery_member_roles(self, target: disnake.Member) -> None:
        self.in_recovery.append(target)

        outdated, added = self.get_roles_changes(target)
        guild = target.guild

        outdated = filter_assignable(list(outdated), guild)
        added = filter_assignable(list(added), guild)

        await target.add_roles(*outdated, reason='Recovery')
        await target.remove_roles(*added, reason='Recovery')

        self.in_recovery.remove(target)

    @commands.Cog.listener()
    async def on_member_update(
        self,
        before: disnake.Member,
        after: disnake.Member,
    ) -> None:
        if before.roles != after.roles and len(after.roles) > 0:
            self.update_saved_roles(after)

    @commands.Cog.listener()
    async def on_member_join(
        self,
        member: disnake.Member,
    ) -> None:
        await self.recovery_member_roles(member)


def setup(bot) -> None:
    bot.add_cog(RoleControllerCog(bot))
