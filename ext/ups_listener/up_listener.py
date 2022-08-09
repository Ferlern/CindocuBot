import asyncio

import disnake
from disnake.ext import commands

from utils.utils import DefaultEmbed
from core import MemberDataController
from main import SEBot

UP_MESSAGES_CHECKS = {
    464272403766444044: lambda embed: embed.color.value == 4437377,
    575776004233232386: lambda embed: embed.description.startswith('Вы успешно лайкнули'),
}


class UpListenerCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        check = UP_MESSAGES_CHECKS.get(message.author.id)
        if not check:
            return

        if message.author.id == 464272403766444044:
            await asyncio.sleep(0.5)
            message = await message.channel.fetch_message(message.id)

        if not message.embeds:
            return

        if not check(message.embeds[0]):
            return

        member_data = MemberDataController(message.author.id)
        member_data.change_balance(25)
        member_data.save()

        await message.channel.send(reference=message, embed=DefaultEmbed(
            title='Спасибо за поддержку!',
            description=f'вам начислено 25 {self.bot.config["coin"]} за ап сервера',
        ))

    @commands.Cog.listener()
    async def on_socket_raw_receive(self, msg):
        print(msg)


def setup(bot):
    bot.add_cog(UpListenerCog(bot))
