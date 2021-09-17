import discord
from utils.utils import DefaultEmbed, display_time


async def mail(ctx,
               member: discord.Member,
               action: str,
               reason,
               time=None,
               additional_description=None):
    description = f"Moderator `{ctx.author.name}` **{action}** you on `{ctx.guild.name}`"
    if time:
        description += f"\n\nDuration: {display_time(time, granularity=4, full=True)}"
    else:
        description += "\n"
    description += f"\nReason: **{reason}**"
    if additional_description:
        description += f"\n\n{additional_description}"
    embed = DefaultEmbed(
        title=f"You was {action}",
        description=description,
    )
    try:
        await member.send(embed=embed)
    except:
        pass
