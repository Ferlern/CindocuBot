import discord
from core import Shop_roles
from discord.ext import commands
from discord.ext.commands.errors import BadArgument
from main import SEBot
from peewee import DoesNotExist
from utils.utils import DefaultEmbed

from ..utils.checks import is_admin


class economy_control(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await is_admin().predicate(ctx)

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.message.delete()
            embed = DefaultEmbed(title="Failed to complete action",
                                 description=f"**Error**: {error}")
            await ctx.send(embed=embed)

    @commands.command()
    async def add_role(self, ctx, role: discord.Role, price: int):
        await ctx.message.delete()
        id = role.id
        coin = self.bot.config["coin"]
        Shop_roles.create(role_id=id, price=price)
        await ctx.send(embed=DefaultEmbed(
            description=
            f'role {role} successfully added to the shop with price {price} {coin}'
        ))

    @commands.command()
    async def remove_role(self, ctx, role: discord.Role):
        id = role.id
        try:
            shop_role = Shop_roles.get(role_id=id)
        except DoesNotExist:
            raise BadArgument("Can't find such role in the shop")
        await ctx.message.delete()
    
        shop_role.delete_instance()
        embed = DefaultEmbed(
            description=f'role {role} successfully deleted from the shop')
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(economy_control(bot))
