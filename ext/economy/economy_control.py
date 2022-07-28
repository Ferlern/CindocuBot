import discord
from core import ShopRoles, MemberDataController
from discord.ext import commands
from discord.ext.commands.errors import BadArgument
from main import SEBot
from peewee import DoesNotExist
from utils.utils import DefaultEmbed

from ..utils.checks import is_admin
from ..utils.converters import NotBotMember


class EconomyControlCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await is_admin().predicate(ctx)

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.message.delete()
            _ = ctx.get_translator()

            embed = DefaultEmbed(title=_("Failed to complete action"),
                                 description=_("**Error**: {error}").format(error=error))
            await ctx.send(embed=embed)

    @commands.command()
    async def add_role(self, ctx, role: discord.Role, price: int):
        await ctx.message.delete()
        _ = ctx.get_translator()

        id = role.id
        coin = self.bot.config["coin"]
        ShopRoles.create(role_id=id, price=price)
        await ctx.send(embed=DefaultEmbed(
            description=_('role {role} successfully added to the shop with price {price} {coin}').format(coin=coin, role=role, price=price)
        ))

    @commands.command()
    async def remove_role(self, ctx, role: discord.Role):
        await ctx.message.delete()
        _ = ctx.get_translator()

        id = role.id
        try:
            shop_role = ShopRoles.get(role_id=id)
        except DoesNotExist:
            raise BadArgument(_("Can't find such role in the shop"))
        await ctx.message.delete()
    
        shop_role.delete_instance()
        embed = DefaultEmbed(
            description=_('Role {role} successfully deleted from the shop').format(role=role))
        await ctx.send(embed=embed)

    @commands.command(aliases=['ac'])
    async def add_coins(self, ctx, member: NotBotMember, amount: int):
        member_data = MemberDataController(member.id)
        
        if -amount > member_data.balance:
            amount = -member_data.balance
        
        member_data.change_balance(amount)
        member_data.save()
        await ctx.tick(True)

def setup(bot):
    bot.add_cog(EconomyControlCog(bot))
