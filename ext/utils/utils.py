import asyncio

from utils.custom_errors import WaitError


def to_string(members):
    return ", ".join([member.mention for member in members])


def to_string_with_ids(members):
    return "\n".join([
        f"{index}. `{member.name}#{member.discriminator}` ({member.id})"
        for index, member in enumerate(members, 1)
    ])


async def wait_for_message(bot, ctx):
    def msg_check(m):
        return m.channel == ctx.message.channel and m.author != bot.user

    try:
        msg = await bot.wait_for('message', timeout=30, check=msg_check)
        await msg.delete()
    except asyncio.TimeoutError:
        raise WaitError
    return msg.content


async def wait_message_from_author(bot, interaction, author_id):
    def msg_check(m):
        return m.channel == interaction.message.channel and m.author.id == author_id

    try:
        msg = await bot.wait_for('message', timeout=30, check=msg_check)
        await msg.delete()
    except asyncio.TimeoutError:
        raise WaitError
    return msg.content
