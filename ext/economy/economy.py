import time

from core import Member_data_controller, Shop_roles
from discord.ext import commands
from discord.utils import get
from discord_components import Interaction
from discord_components.component import Select, SelectOption
from main import SEBot
from utils.custom_errors import (MaxBitrateReached, MaxSlotsAmount,
                                 NotEnoughMoney)
from utils.utils import DefaultEmbed, TimeConstans

from ..utils import Interaction_inspect
from ..utils.build import (build_page_components, get_last_page,
                           page_implementation, update_message)

next_bitrate = {'64': 96, '96': 128, '128': 192, '192': 256, '256': 384}


class economyCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    def build_role_shop_embed(self, items, page):
        coin = self.bot.config["coin"]
        if items:
            description = '\n\n'.join([
                f"{index}. <@&{role['role_id']}> — {role['price']} {coin}"
                for index, role in enumerate(items, 1)
            ])
            buy_select = Select(
                id='economy_buy_select',
                placeholder="Select an item to buy",
                options=[
                    SelectOption(
                        label=f"{index}",
                        value=str(index - 1 + page * 10),
                        description=f"buy it for {role['price']} coins")
                    for index, role in enumerate(items, 1)
                ])
        else:
            buy_select = []
            description = 'There are no roles in the shop.'
        embed = DefaultEmbed(title='Roles shop', description=description)
        return embed, buy_select

    def build_voice_shop_embed(self, values: dict):
        coin = self.bot.config["coin"]
        config = self.bot.config['personal_voice']
        member = Member_data_controller(id=values['author'])
        current_voice = member.user_info.user_personal_voice
        embed = DefaultEmbed(
            title='Private voice shop',
            description=
            'Here you can buy a personal voice channel on the server and "upgrade" it'
        )

        if len(current_voice) > 0:
            current_voice = member.user_info.user_personal_voice[0]
            slots = current_voice.slots
            max_bitrate = current_voice.max_bitrate
            try:
                to_bitrate = next_bitrate[str(max_bitrate)]
            except KeyError:
                to_bitrate = 999999999
            bitrate_price = int(
                (to_bitrate - max_bitrate) / 32 * config['bitrate_price'])

            value = f"**{slots}** -> **{slots + 1}** for **{slots * config['slot_price']}** {coin}" if slots < 25 else 'MAX'
            embed.add_field(
                name='1. Increase the number of slots',
                value=value,
            )

            value = f"**{max_bitrate}**kbps -> **{to_bitrate}**kbps for **{bitrate_price}** {coin}" if max_bitrate <= 256 else 'MAX'
            embed.add_field(name='2. Increase max bitrate', value=value)
            options = []
            if slots <= 25:
                options.append(
                    SelectOption(
                        label='Increase the number of slots',
                        value='slot',
                        description=
                        f"{slots} -> {slots + 1} for {slots * config['slot_price']} coins\nThe price grows with each slot",
                    ))
            if max_bitrate <= 256:
                options.append(
                    SelectOption(
                        label='Increase max bitrate',
                        value='bitrate',
                        description=
                        f"{max_bitrate}kbps -> {to_bitrate}kbps for {bitrate_price} coins",
                    ))
            if options:
                buy_select = Select(id='economy_buy_select',
                                    placeholder="Select an item to buy",
                                    options=options)
            else:
                buy_select = []
        else:
            embed.add_field(
                name='1. Personal voice channel',
                value=
                f"Your channel will be placed in the category <#{config.get('categoty')}>\n{config['price']} {coin}"
            )
            buy_select = Select(id='economy_buy_select',
                                placeholder="Select an item to buy",
                                options=[
                                    SelectOption(
                                        label='Personal voice channel',
                                        value='channel')
                                ])

        return embed, buy_select

    def shop_builder(self, values: dict):
        if values['selected'] == 'role':
            roles = Shop_roles.select().order_by(Shop_roles.price)
            last_page = get_last_page(roles)
            page, last_page, actual_roles = page_implementation(values, roles)
            page_components = build_page_components(page, last_page,
                                                    'economyshop')
            embed, components = self.build_role_shop_embed(actual_roles, page)
        elif values['selected'] == 'voice':
            embed, components = self.build_voice_shop_embed(values)
            page_components = None

        page_components = [page_components] if page_components else []
        select_shop = Select(
            id='economyshop_select_type',
            placeholder='Select shop type',
            options=[
                SelectOption(
                    label='roles shop',
                    value='role',
                    description='Here you can purchase roles for coins',
                    default=values['selected'] == 'role'),
                SelectOption(
                    label='voice shop',
                    value='voice',
                    description=
                    'Here you can buy a personal voice channel for coins',
                    default=values['selected'] == 'voice')
            ])
        page_components.append(select_shop)
        if components:
            page_components.append(components)
            components = page_components
        else:
            components = page_components

        return embed, components, values

    async def buy_item(self, interaction: Interaction):
        await Interaction_inspect.only_author(interaction)

        member = Member_data_controller(interaction.author.id)

        to_buy = interaction.values[0]
        coin = self.bot.config['coin']
        try:
            to_buy = int(to_buy)
            member_roles = member.roles

            roles = Shop_roles.select().order_by(
                Shop_roles.price)
            roles = list(roles.dicts().execute())
            
            role_to_buy = roles[to_buy]
                
            if role_to_buy['role_id'] in member_roles:
                await interaction.respond(
                    content=
                    f"It looks like you already have this role! If for some reason you don't have it, use {self.bot.config['prefixes'][0]}sync"
                )
                return
            elif role_to_buy['price'] > member.balance:
                await interaction.respond(
                    content=
                    f"You need {role_to_buy['price'] - member.balance} more {coin} to buy this role"
                )
                return
            else:
                member.change_balance(-role_to_buy['price'])
                
                guild = interaction.author.guild
                role = guild.get_role(role_to_buy['role_id'])
                if not role:
                    await interaction.respond(content="I can't find this role. It may have been deleted")
                    return
                
                member.save()
                
                await interaction.author.add_roles(
                    role, reason='successful purchase in the shop')
                await interaction.respond(
                    content=
                    f"Role <@&{role.id}> was successfully purchased for {role_to_buy['price']} {coin}. I hope you like it, because you can't sell it :)"
                )

        except ValueError:
            config = self.bot.config['personal_voice']
            try:
                if to_buy == 'channel':
                    if member.balance >= config['price']:
                        if member.user_info.user_personal_voice:
                            await interaction.respond(
                                content='You already have voice channel')
                            return
                        category = get(interaction.guild.categories,
                                       id=config['categoty'])
                        voice = await interaction.author.guild.create_voice_channel(
                            name=interaction.author.name,
                            category=category,
                            user_limit=5)
                        member.create_private_voice(voice.id)
                        member.change_balance(-config['price'])
                        member.save()
                        await interaction.respond(
                            content=
                            f"Your personal voice channel has been created!"
                        )
                    else:
                        await interaction.respond(
                            content=
                            f"You don't have enough {coin} to make a purchase")
                elif to_buy == 'slot':
                    member.buy_slot(config['slot_price'])
                    await interaction.respond(content=f"New slot added")
                elif to_buy == 'bitrate':
                    member.buy_bitrate(config['bitrate_price'])
                    await interaction.respond(
                        content=f"The maximum bitrate has been increased")
                else:
                    raise ValueError(f"can't find such item for buy: {to_buy}")
            except NotEnoughMoney:
                await interaction.respond(
                    content=f"You don't have enough {coin} to make a purchase")
            except MaxSlotsAmount:
                await interaction.respond(content=f"Maximum slots reached")
            except MaxBitrateReached:
                await interaction.respond(content=f"Maximum bitrate reached")

    @commands.Cog.listener()
    async def on_button_click(self, ctx: Interaction):
        component = ctx.component
        id: str = component.id
        if not id.startswith("economy"):
            return

        await update_message(self.bot, self.shop_builder, ctx)

    @commands.Cog.listener()
    async def on_select_option(self, ctx: Interaction):
        component = ctx.component
        id: str = component.id
        if not id.startswith("economy"):
            return

        if not id.startswith("economy_buy"):
            await update_message(self.bot, self.shop_builder, ctx)
        else:
            await self.buy_item(ctx)
            values = Interaction_inspect.get_values(ctx)
            embed, components, values = self.shop_builder(values)
            components = Interaction_inspect.inject(components, values)
            await ctx.message.edit(embed=embed, components=components)

    @commands.command()
    @commands.cooldown(1, TimeConstans.day, commands.BucketType.user)
    async def daily(self, ctx):
        await ctx.message.delete()
        daily = self.bot.config["daily"]
        coin = self.bot.config["coin"]

        member = Member_data_controller(ctx.author.id)
        member.change_balance(daily)
        member.save()

        description = f"{daily} {coin} have been successfully transferred to your balance. Now you have {member.balance} {coin}"
        description += f"\n\nYou can get the bonus again <t:{int(time.time() + TimeConstans.day)}:R>"

        embed = DefaultEmbed(title="Daily bonus received!",
                             description=description)
        embed.set_thumbnail(url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @daily.error
    async def daily_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            embed = DefaultEmbed(
                title="Bonus not available yet",
                description=
                f"Your today's bonus has already been received.\n\nYou can get the bonus again <t:{int(time.time() + error.retry_after)}:R>"
            )

            embed.set_thumbnail(url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @commands.command()
    async def shop(self, ctx, type='role'):
        await ctx.message.delete()
        type = 'voice' if type in ['vc', 'voice', 'channel', 2] else 'role'
        values = {'author': ctx.author.id, 'page': 0, 'selected': type}
        embed, components, values = self.shop_builder(values)
        components = Interaction_inspect.inject(components, values)
        await ctx.send(embed=embed, components=components)


def setup(bot):
    bot.add_cog(economyCog(bot))
