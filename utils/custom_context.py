import asyncio
from discord.ext import commands

from utils.checks import confirm_check
from utils.custom_errors import ConfirmationError
from discord_components import Button


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def confirm(self, *args, **kwargs):
        kwargs['components'] = kwargs.get('components', [Button(label="confirm")])
        msg = await super().send(*args, **kwargs)
        try:
            interaction = await self.bot.wait_for('button_click',
                                                  timeout=120,
                                                  check=confirm_check(self))
            await interaction.respond(type=7, components=[])
            return msg
        except asyncio.TimeoutError:
            component = msg.components[0].components[0]
            component.style = 4
            component.disabled = True
            await msg.edit(components=[component])

            raise ConfirmationError

    async def tick(self, opt: bool):
        lookup = {
            True: '✅',
            False: '❌',
            None: '❔',
        }
        emoji = lookup.get(opt, '❔')
        await self.message.add_reaction(emoji)
