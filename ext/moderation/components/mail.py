import discord
from utils.utils import DefaultEmbed, display_time


async def mail(ctx,
               member: discord.Member,
               action: str,
               reason,
               time=None,
               additional_description=None):
    translator = ctx.get_translator()
    _ = translator
    description = _("Moderator `{author_name}` **{action}** you on `{guild_name}`").format(
        author_name=ctx.author.name,
        action=action,
        guild_name=ctx.guild.name,
    )
    if time:
        description += _("\n\nDuration: {duration}").format(
            duration=display_time(translator, time, granularity=4, full=True)
        )
    else:
        description += "\n"
    description += _("\nReason: **{reason}**").format(reason=reason)
    if additional_description:
        description += f"\n\n{additional_description}"
    embed = DefaultEmbed(
        title=_("You was {action}").format(action=action),
        description=description,
    )
    try:
        await member.send(embed=embed)
    except:
        pass
