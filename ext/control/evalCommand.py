import os
import sys
import time
from inspect import getsource

import discord
from discord.ext import commands
from ..utils.checks import is_owner

codes = []


class EvalCommandCog(commands.Cog):
    def __init__(self):
        pass

    def resolve_variable(self, variable):
        if hasattr(variable, "__iter__"):
            var_length = len(list(variable))
            if (var_length > 100) and (not isinstance(variable, str)):
                return f"{type(variable).__name__} с более чем 100 значений ({var_length})"
            elif (not var_length):
                return f"<пустой {type(variable).__name__}"

        if (not variable) and (not isinstance(variable, bool)):
            return f"пустой {type(variable).__name__} объект"
        return (variable if (len(f"{variable}") <= 1000) else
                f"{type(variable).__name__} длинны {len(f'{variable}')}")

    def prepare(self, string):
        arr = string.strip("```").replace("py\n", "").replace("python\n",
                                                              "").split("\n")
        if not arr[::-1][0].replace(" ", "").startswith("return"):
            arr[len(arr) - 1] = "return " + arr[::-1][0]
        return "".join(f"\n\t{i}" for i in arr)

    @commands.command(aliases=['eval', 'exec', 'evaluate'])
    @is_owner()
    async def _eval(self, ctx, *, code: str):
        global codes
        codes.append(code)
        if len(codes) > 30:
            codes.pop(0)
        if "TOKEN" in code or "token" in code:
            return
        silent = ("-s" in code)

        code = self.prepare(code.replace("-s", ""))
        args = {
            "discord": discord,
            "sauce": getsource,
            "sys": sys,
            "os": os,
            "imp": __import__,
            "this": self,
            "ctx": ctx
        }

        try:
            exec(f"async def func():{code}", args)
            a = time.time()
            response = await eval("func()", args)
            if silent or (response is None) or isinstance(
                    response, discord.Message):
                del args, code
                return
            embed = discord.Embed(
                title="🔮 Выполнено успешно",
                description=f"```py\n{self.resolve_variable(response)}```",
                colour=discord.Colour.purple())
            embed.set_footer(
                text=
                f"⏱️ {type(response).__name__} | {(time.time() - a) / 1000} ms"
            )
            embed.set_thumbnail(url=ctx.author.avatar_url)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="🪡 Ошибка",
                description=f"```{type(e).__name__}: {str(e)}```",
                colour=discord.Colour.purple())
            embed.set_thumbnail(url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

        del args, code, silent

    @commands.command(pass_context=True, aliases=['code'])
    @is_owner()
    async def _last_code(self, ctx, index=1):
        code: str
        try:
            code = codes[-index]
        except:
            await ctx.send(f"Код не найден. Сохранено запросов: {len(codes)}")
        else:
            code = f'```py\n{code}```' if not code.startswith("```") else code
            await ctx.send(code)


def setup(bot):
    bot.add_cog(EvalCommandCog())
