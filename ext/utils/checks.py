from discord.ext import commands


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


def owner_or_permissions(**perms):
    original = commands.has_permissions(**perms).predicate

    async def extended_check(ctx):
        is_owner = await ctx.bot.is_owner(ctx.author)
        if ctx.guild is None:
            return False
        return ctx.guild.owner_id == ctx.author.id or await original(
            ctx) or is_owner

    return commands.check(extended_check)


def is_owner():
    async def pred(ctx):
        is_owner = await ctx.bot.is_owner(ctx.author)
        return ctx.guild.owner_id == ctx.author.id or is_owner

    return commands.check(pred)


def is_admin():
    async def pred(ctx):
        return await owner_or_permissions(administrator=True).predicate(ctx)

    return commands.check(pred)


def is_mod(mod_roles):
    first = is_admin().predicate
    second = commands.has_any_role(*mod_roles).predicate

    async def pred(ctx):
        return await first(ctx) or await second(ctx)

    return commands.check(pred)