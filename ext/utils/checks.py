from discord.ext import commands
from discord.ext.commands.errors import MissingPermissions, NoPrivateMessage


async def check_guild_permissions(ctx, perms, *, check=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    if ctx.guild is None:
        return False

    resolved = ctx.author.guild_permissions
    return check(
        getattr(resolved, name, None) == value
        for name, value in perms.items())

def is_owner():
    async def pred(ctx):
        if ctx.guild is None:
            return False
        
        is_owner = await ctx.bot.is_owner(ctx.author)
        return ctx.guild.owner_id == ctx.author.id or is_owner

    return commands.check(pred)

def owner_or_permissions(**perms):
    first = is_owner().predicate
    second = commands.has_permissions(**perms).predicate
    
    async def extended_check(ctx):
        try:
            return await first(ctx) or await second(ctx)
        except MissingPermissions:
            return

    return commands.check(extended_check)

def is_admin():
    async def pred(ctx):
        return await owner_or_permissions(administrator=True).predicate(ctx)

    return commands.check(pred)


def is_mod():
    first = is_admin().predicate
    
    async def pred(ctx):
        try:
            return await first(ctx) or await commands.has_any_role(*ctx.bot.config["moderators_roles"]).predicate(ctx)
        except NoPrivateMessage:
            return False

    return commands.check(pred)