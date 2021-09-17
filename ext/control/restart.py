import sys
import traceback

from bot_components.configurator import configurator
from core import create_database
from core_elements.data_controller.models import close_connection
from discord.ext import commands
from main import SEBot

from ..utils.checks import is_owner


class RestartCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await is_owner().predicate(ctx)

    @commands.command(aliases=['re'])
    async def restart(self, ctx):
        exception = True
        for extension in self.bot.system['initial_extensions']:
            if 'RestartCog' in extension:
                continue
            try:
                self.bot.unload_extension(extension)
            except Exception as e:
                print(f'Failed to unload extension {extension}.',
                      file=sys.stderr)
                traceback.print_exc()
                exception = False
            try:
                self.bot.load_extension(extension)
            except Exception as e:
                print(f'Failed to load extension {extension}.',
                      file=sys.stderr)
                traceback.print_exc()
                exception = False
        await ctx.tick(exception)

    @commands.command(aliases=['rdb'])
    async def clear_data(self, ctx):
        try:
            close_connection()
            create_database("./core_elements/data_controller/data.db")
        except Exception as e:
            print(f'Failed to clear data.', file=sys.stderr)
            traceback.print_exc()
            await ctx.tick(False)
        else:
            await ctx.tick(True)

    @commands.command(aliases=['rc'])
    async def reload_config(self, ctx):
        try:
            configurator.load()
            configurator.dump()
            self.bot.reload_config()
        except Exception as e:
            print(f'Failed to reload config.', file=sys.stderr)
            traceback.print_exc()
            await ctx.tick(False)
        else:
            await ctx.tick(True)


def setup(bot):
    bot.add_cog(RestartCog(bot))
