import os
import sys
import time
from inspect import getsource
import disnake
from disnake.ext import commands
from ..utils.checks import is_owner
from utils.utils import DefaultEmbed
from core_elements.data_controller import models
from core_elements import code as saved_codes_controller

codes = []


def codes_to_string(codes) -> str:
    return ' '.join([f'`{code["name"]}`' for code in codes])


class EvalCommandCog(commands.Cog):
    def __init__(self):
        pass
    
    async def cog_check(self, ctx):
        return await is_owner().predicate(ctx)

    def resolve_variable(self, variable):
        if hasattr(variable, "__iter__"):
            var_length = len(list(variable))
            if (var_length > 100) and (not isinstance(variable, str)):
                return f"{type(variable).__name__} с более чем 100 значений ({var_length})"
            elif (not var_length):
                return f"<пустой {type(variable).__name__}"

        if (not variable) and (not isinstance(variable, bool)):
            return f"пустой {type(variable).__name__} объект"
        return (variable if (len(f"{variable}") <= 1024) else
                f"{type(variable).__name__} длинны {len(f'{variable}')}")

    def prepare(self, string):
        arr = string.strip("```").replace("py\n", "").replace("python\n",
                                                              "").split("\n")
        if not arr[::-1][0].replace(" ", "").startswith("return"):
            arr[len(arr) - 1] = "return " + arr[::-1][0]
        return "".join(f"\n\t{i}" for i in arr)

    async def evaluate(self, ctx, code):
        global codes
        codes.append(code)
        if len(codes) > 30:
            codes.pop(0)
        if "TOKEN" in code or "token" in code:
            return
        silent = ("-s" in code)

        code = self.prepare(code.replace("-s", ""))
        args = {
            "disnake": disnake,
            "sauce": getsource,
            "sys": sys,
            "os": os,
            "imp": __import__,
            "self": self,
            "ctx": ctx,
            "conn": models.conn
        }

        try:
            exec(f"async def func():{code}", args)
            a = time.time()
            response = await eval("func()", args)
            if silent or (response is None) or isinstance(
                    response, disnake.Message):
                del args, code
                return
            embed = disnake.Embed(
                title="🔮 Выполнено успешно",
                description=f"```py\n{self.resolve_variable(response)}```",
                colour=disnake.Colour.purple())
            embed.set_footer(
                text=
                f"⏱️ {type(response).__name__} | {(time.time() - a) / 1000} ms"
            )
            embed.set_thumbnail(url=ctx.author.avatar.url)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = disnake.Embed(
                title="🪡 Ошибка",
                description=f"```{type(e).__name__}: {str(e)}```",
                colour=disnake.Colour.purple())
            embed.set_thumbnail(url=ctx.author.avatar.url)
            await ctx.send(embed=embed)

        del args, code, silent
    
    @commands.command(aliases=['eval', 'exec', 'evaluate'])
    async def _eval(self, ctx, *, code: str):
        if saved_codes := saved_codes_controller.get_saved_codes(code):
            for code in saved_codes:
                await self.evaluate(ctx, code['code'])
        else:
            await self.evaluate(ctx, code)
        
        
    @commands.command()
    async def _last_code(self, ctx, index=1):
        code: str
        try:
            code = codes[-index]
        except:
            await ctx.send(f"Код не найден. Сохранено запросов: {len(codes)}")
        else:
            code = f'```py\n{code}```' if not code.startswith("```") else code
            await ctx.send(code)
            
    @commands.command()
    async def savecode(self, ctx, name: str, *, code: str):
        saved_codes_controller.save_code(code, name)
        await ctx.tick(True)
        
    @commands.command()
    async def setgroup(self, ctx, name: str, group: str):
        saved_codes_controller.change_group(name, group)
        await ctx.tick(True)
        
    @commands.command()
    async def rename(self, ctx, old_name: str, new_name: str):
        saved_codes_controller.change_name(old_name, new_name)
        await ctx.tick(True)
        
    @commands.command()
    async def deletecode(self, ctx, name: str):
        saved_codes_controller.delete_codes(name)
        await ctx.tick(True)
        
    @commands.command()
    async def showcode(self, ctx, name: str = "Show All"):
        _ = ctx.get_translator()
        
        codes = saved_codes_controller.get_saved_codes(name)
        amount = len(codes)
        
        embed = DefaultEmbed()
        if amount == 0:
            embed.title = _('Nothing to show. Existing codes:')
            embed.description = codes_to_string(saved_codes_controller.get_all())
        elif amount == 1:
            code = codes[0]
            embed.title = _("Name: {name}; Group: {group}").format(name=code['name'], group=code['group'])
            embed.description = code['code']
        else:
            embed.title = _("Group {group}").format(group=name)
            embed.description = codes_to_string(codes)
        
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(EvalCommandCog())
