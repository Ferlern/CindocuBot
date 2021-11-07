import logging
import math
import psutil
import time

from discord.ext import commands
from main import SEBot
from utils.utils import DefaultEmbed, display_time

from ..utils.checks import is_owner

logger = logging.getLogger('Arctic')


def convert_size(size_bytes: int) -> str:
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

class Status(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await is_owner().predicate(ctx)

    @commands.command()
    async def status(self, ctx):
        await ctx.message.delete()
        RAM_statistic = psutil.virtual_memory()
        RAM_statistic_str = f"**total**: {convert_size(RAM_statistic.used)}/{convert_size(RAM_statistic.total)} ({RAM_statistic.percent}% used)"
        
        p = psutil.Process()
        with p.oneshot():
            process_RAM_load_percent = p.memory_percent()
            process_RAM_load = convert_size(process_RAM_load_percent * RAM_statistic.total / 100)
            process_RAM_load_str = f"**by bot**: {process_RAM_load} ({round(process_RAM_load_percent, 2)}%)"
        
        memory_used = 0
        memory_total = 0
        for disk in psutil.disk_partitions():
            try:
                memory_used += psutil.disk_usage(disk.device).used
                memory_total += psutil.disk_usage(disk.device).total
            except PermissionError:
                pass
        percent = memory_used / memory_total
        memory_str = f"{convert_size(memory_used)}/{convert_size(memory_total)} ({round(percent, 2)}% used)"
        
        total_CPU_statistic_load = psutil.cpu_percent()
        CPUs_load = psutil.cpu_percent(percpu=True)
        
        CPU_count_str = f"{psutil.cpu_count(logical=False)} ({psutil.cpu_count()} virtual) cores."
        CPU_load_str = f"\nLoad per core: {', '.join(str(load) for load in CPUs_load)}\nSummury: {total_CPU_statistic_load}"
        CPU_str = CPU_count_str + CPU_load_str
        
        main_state = f"Ping: {round(self.bot.latency * 1000)}ms"
        main_state += f"\nUptime: {display_time(time.time() - self.bot.uptime, granularity=4, full=False)}"
        
        embed = DefaultEmbed(title = 'Status', description=main_state)
        embed.add_field(
            name="RAM usage",
            value=RAM_statistic_str + '\n' + process_RAM_load_str,
            inline=False
        )
        embed.add_field(
            name="Memory usage",
            value=memory_str,
            inline=False
        )
        embed.add_field(
            name="CPU usage",
            value=CPU_str,
            inline=False
        )
        
        await ctx.send(embed = embed)


def setup(bot):
    bot.add_cog(Status(bot))
