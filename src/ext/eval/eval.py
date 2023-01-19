import os
import sys
import time
from inspect import getsource
import disnake
from disnake.ext import commands

from src.database.models import psql_db


class EvalCommandCog(commands.Cog):
    async def cog_check(self, ctx) -> bool:  # pylint:disable=invalid-overridden-method
        return await ctx.bot.is_owner(ctx.author)

    def prepaire_response(self, variable) -> str:
        text = repr(variable)
        cutted_text = text[:1024]
        return f"```py\n{cutted_text}\n```{len(cutted_text)}/{len(text)}"

    def prepare(self, string: str) -> str:
        arr = string.strip("`").removeprefix('py\n').splitlines()
        # last_line = arr[-1]
        # if not last_line.split()[0] == "return":
        #     last_without_indent = last_line.lstrip()
        #     arr[-1] = (f"{last_line[:-len(last_without_indent)]}"
        #                f"return {last_without_indent}")
        return "".join(f"\n\t{i}" for i in arr)

    async def evaluate(self, ctx: commands.Context, code: str) -> None:
        code = self.prepare(code)
        args = {
            "disnake": disnake,
            "sauce": getsource,
            "sys": sys,
            "os": os,
            "imp": __import__,
            "self": self,
            "ctx": ctx,
            "conn": psql_db
        }

        try:
            exec(f"async def func():{code}", args)  # pylint: disable=exec-used
            start_time = time.time()
            response = await eval("func()", args)  # pylint: disable=eval-used

            if response is None or isinstance(response, disnake.Message):
                return

            embed = disnake.Embed(
                title="🔮 Выполнено успешно",
                description=self.prepaire_response(response),
                colour=disnake.Colour.purple())
            embed.set_footer(
                text=(f"⏱️ {type(response).__name__} | {(time.time() - start_time) / 1000} ms")
            )
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
        except Exception as error:  # pylint: disable=broad-except
            embed = disnake.Embed(
                title="🪡 Ошибка",
                description=f"```{type(error).__name__}: {str(error)}```",
                colour=disnake.Colour.purple())
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)

    @commands.command(aliases=['eval', 'exec', 'evaluate'])
    async def _eval(self, ctx, *, code: str) -> None:
        await self.evaluate(ctx, code)


def setup(bot) -> None:
    bot.add_cog(EvalCommandCog())
