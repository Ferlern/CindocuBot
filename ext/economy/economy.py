from core import MemberDataController, ShopRoles
from disnake.ext import commands
from disnake.utils import get
from discord_components import Interaction
from discord_components.component import Select, SelectOption
from main import SEBot
from utils.custom_errors import (MaxBitrateReached, MaxSlotsAmount,
                                 NotEnoughMoney, BonusAlreadyReceived)
from utils.utils import DefaultEmbed, get_seconds_until_new_day, next_bitrate

from ..utils import Interaction_inspect
from ..utils.build import (build_page_components, get_last_page,
                           page_implementation, update_message)
from ..utils.converters import InteractedMember, NaturalNumber


class EconomyCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot
        self.economy_emoji = self.bot.config['additional_emoji']['economy']
        
    async def cog_command_error(self, ctx, error):
        _ = ctx.get_translator()
        if isinstance(error, commands.BadArgument):
            await ctx.message.delete()

            embed = DefaultEmbed(title=_("Failed to complete action"),
                                 description=_("**Error**: {error}").format(error=error))
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.delete()

            embed = DefaultEmbed(
                title=_("Failed to complete action"),
                description=_("**Error**: {error} not specified").format(error=error.param.name)
            )
            await ctx.send(embed=embed)

    def build_role_shop_embed(self, translator, items, page):
        _ = translator
        coin = self.bot.config["coin"]
        if items:
            description = '\n\n'.join([
                f"{index}. <@&{role['role_id']}> — {role['price']} {coin}"
                for index, role in enumerate(items, 1)
            ])
            buy_select = Select(
                id='economy_buy_select',
                placeholder=_("Select an item to buy"),
                options=[
                    SelectOption(
                        label=f"{index}",
                        value=str(index - 1 + page * 10),
                        description=_("buy it for {price} coins").format(price=role['price']))
                    for index, role in enumerate(items, 1)
                ])
        else:
            buy_select = []
            description = _('There are no roles in the shop.')
        embed = DefaultEmbed(title=_('{emoji} Roles shop').format(emoji=self.economy_emoji["roles_shop"]), description=description)
        return embed, buy_select

    def build_voice_shop_embed(self, translator, values: dict):
        _ = translator
        coin = self.bot.config["coin"]
        config = self.bot.config['personal_voice']
        member = MemberDataController(id=values['author'])
        current_voice = member.user_info.user_personal_voice
        embed = DefaultEmbed(
            title=_('{emoji} Private voice shop').format(emoji=self.economy_emoji["voice_shop"]),
            description=_('Here you can buy a personal voice channel on the server and "upgrade" it')
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

            value = _("**{slots}** -> **{next_slot}** for **{price}** {coin}").format(
                slots=slots,
                next_slot = slots + 1,
                price=config['slot_price'] * slots,
                coin=coin,
            ) if slots < 25 else _('MAX')
            embed.add_field(
                name=_('1. Increase the number of slots'),
                value=value,
            )

            value = _("**{max_bitrate}**kbps -> **{to_bitrate}**kbps for **{bitrate_price}** {coin}").format(
                max_bitrate=max_bitrate,
                to_bitrate=to_bitrate,
                bitrate_price=bitrate_price,
                coin=coin,
            ) if max_bitrate <= 256 else _('MAX')
            embed.add_field(name=_('2. Increase max bitrate'), value=value)
            options = []
            if slots <= 25:
                options.append(
                    SelectOption(
                        label=_('Increase the number of slots'),
                        value='slot',
                        description=_("{slots} -> {next_slot} for {price} coins\nThe price grows with each slot").format(
                            slots=slots,
                            next_slot = slots + 1,
                            price=config['slot_price'] * slots,
                        ),
                    ))
            if max_bitrate <= 256:
                options.append(
                    SelectOption(
                        label=_('Increase max bitrate'),
                        value='bitrate',
                        description=_("{max_bitrate}kbps -> {to_bitrate}kbps for {bitrate_price} coins").format(
                            max_bitrate=max_bitrate,
                            to_bitrate=to_bitrate,
                            bitrate_price=bitrate_price,
                        ),
                    ))
            if options:
                buy_select = Select(id='economy_buy_select',
                                    placeholder=_("Select an item to buy"),
                                    options=options)
            else:
                buy_select = []
        else:
            embed.add_field(
                name=_('1. Personal voice channel'),
                value=_("Your channel will be placed in the category <#{cathegory}>\n{price} {coin}").format(
                    cathegory=config.get('categoty'),
                    price=config['price'],
                    coin=coin,
                )
            )
            buy_select = Select(id='economy_buy_select',
                                placeholder=_("Select an item to buy"),
                                options=[
                                    SelectOption(
                                        label=_('Personal voice channel'),
                                        value='channel')
                                ])

        return embed, buy_select

    def shop_builder(self, translator, values: dict):
        _ = translator
        if values['selected'] == 'role':
            roles = ShopRoles.select().order_by(ShopRoles.price)
            last_page = get_last_page(roles)
            page, last_page, actual_roles = page_implementation(values, roles)
            page_components = build_page_components(page, last_page,
                                                    'economyshop')
            embed, components = self.build_role_shop_embed(translator, actual_roles, page)
        elif values['selected'] == 'voice':
            embed, components = self.build_voice_shop_embed(translator, values)
            page_components = None

        page_components = [page_components] if page_components else []
        select_shop = Select(
            id='economyshop_select_type',
            placeholder=_('Select shop type'),
            options=[
                SelectOption(
                    label=_('roles shop'),
                    value='role',
                    description=_('Here you can purchase roles for coins'),
                    default=values['selected'] == 'role'),
                SelectOption(
                    label=_('voice shop'),
                    value='voice',
                    description=_('Here you can buy a personal voice channel for coins'),
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
        _ = self.bot.get_translator_by_interaction(interaction)
        await Interaction_inspect.only_author(interaction)

        member = MemberDataController(interaction.author.id)

        to_buy = interaction.values[0]
        coin = self.bot.config['coin']
        try:
            to_buy = int(to_buy)
            member_roles = member.roles

            roles = ShopRoles.select().order_by(
                ShopRoles.price)
            roles = list(roles.dicts().execute())
            
            role_to_buy = roles[to_buy]
                
            if role_to_buy['role_id'] in member_roles:
                await interaction.respond(
                    content=_("It looks like you already have this role! If for some reason you don't have it, use {prefix}sync").format(
                        prefix=self.bot.config['prefixes'][0]
                    )
                )
                return
            elif role_to_buy['price'] > member.balance:
                await interaction.respond(
                    content=_("You need {amount} more {coin} to buy this role").format(
                        amount=role_to_buy['price'] - member.balance,
                        coin=coin,
                    )
                )
                return
            else:
                member.change_balance(-role_to_buy['price'])
                
                guild = interaction.author.guild
                role = guild.get_role(role_to_buy['role_id'])
                if not role:
                    await interaction.respond(content=_("I can't find this role. It may have been deleted"))
                    return
                
                member.save()
                
                await interaction.author.add_roles(
                    role, reason=_('successful purchase in the shop'))
                await interaction.respond(
                    content=_("Role <@&{role_id}> was successfully purchased for {price} {coin}. I hope you like it, because you can't sell it :)").format(
                        role_id=role.id,
                        price=role_to_buy['price'],
                        coin=coin,
                    )
                )

        except ValueError:
            config = self.bot.config['personal_voice']
            try:
                if to_buy == 'channel':
                    if member.balance >= config['price']:
                        if member.user_info.user_personal_voice:
                            await interaction.respond(
                                content=_('You already have voice channel'))
                            return
                        category = get(interaction.guild.categories,
                                       id=config['categoty'])
                        voice = await interaction.author.guild.create_voice_channel(
                            name=interaction.author.name,
                            category=category,
                            user_limit=5)
                        await voice.set_permissions(
                            interaction.author,
                            manage_permissions = True,
                            manage_channels = True
                        )
                        member.create_private_voice(voice.id)
                        member.change_balance(-config['price'])
                        member.save()
                        await interaction.respond(
                            content=_("Your personal voice channel has been created!")
                        )
                    else:
                        await interaction.respond(
                            content=_("You don't have enough {coin} to make a purchase").format(coin=coin))
                elif to_buy == 'slot':
                    member.buy_slot(config['slot_price'])
                    await interaction.respond(content=_("New slot added"))
                elif to_buy == 'bitrate':
                    member.buy_bitrate(config['bitrate_price'])
                    await interaction.respond(
                        content=_("The maximum bitrate has been increased"))
                else:
                    raise ValueError(_("can't find such item for buy: {item}").format(item=to_buy))
            except NotEnoughMoney:
                await interaction.respond(
                    content=_("You don't have enough {coin} to make a purchase").format(coin=coin))
            except MaxSlotsAmount:
                await interaction.respond(content=_("Maximum slots reached"))
            except MaxBitrateReached:
                await interaction.respond(content=_("Maximum bitrate reached"))

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
            translator = self.bot.get_translator_by_interaction(ctx)
            await self.buy_item(ctx)
            values = Interaction_inspect.get_values(ctx)
            embed, components, values = self.shop_builder(translator, values)
            components = Interaction_inspect.inject(components, values)
            await ctx.message.edit(embed=embed, components=components)

    @commands.command(aliases = ['bonus'])
    async def daily(self, ctx):
        await ctx.message.delete()
        _ = ctx.get_translator()

        daily = self.bot.config["daily"]
        coin = self.bot.config["coin"]

        member = MemberDataController(ctx.author.id)
        
        try:
            member.take_bonus(daily)
        except BonusAlreadyReceived:
            embed = DefaultEmbed(
                title=_("{emoji} Bonus not available yet").format(emoji=self.economy_emoji['daily_cooldown']),
                description=
                _("Your today's bonus has already been received.\n\nYou can get the bonus again <t:{seconds}:R>").format(
                    seconds=get_seconds_until_new_day()
                )
            )

            embed.set_thumbnail(url=ctx.author.avatar.url)
            await ctx.send(embed=embed)
            return
            
        member.save()

        description = _("{daily} {coin} have been successfully transferred to your balance. Now you have {balance} {coin}").format(
            daily=daily,
            balance=member.balance,
            coin=coin,
        )
        description += _("\n\nYou can get the bonus again <t:{seconds}:R>").format(
                    seconds=get_seconds_until_new_day()
                )

        embed = DefaultEmbed(title=_("{emoji} Daily bonus received!").format(emoji=self.economy_emoji['daily_recieved']),
                             description=description)
        embed.set_thumbnail(url=ctx.author.avatar.url)

        await ctx.send(embed=embed)

    @commands.command()
    async def shop(self, ctx, type='role'):
        await ctx.message.delete()
        translator = ctx.get_translator()

        type = 'voice' if type in ['vc', 'voice', 'channel', 2] else 'role'
        values = {'author': ctx.author.id, 'page': 0, 'selected': type}
        embed, components, values = self.shop_builder(translator, values)
        components = Interaction_inspect.inject(components, values)
        await ctx.send(embed=embed, components=components)
        
    @commands.command(aliases=['give'])
    async def transfer(self, ctx, member: InteractedMember, amount: NaturalNumber):
        _ = ctx.get_translator()
        coin = self.bot.config['coin']
        author_data = MemberDataController(ctx.author.id)
        member_data = MemberDataController(member.id)
        
        if amount > author_data.balance:
            amount = member_data.balance
            
        author_data.change_balance(-amount)
        member_data.change_balance(amount)
        author_data.save()
        member_data.save()
        
        embed = DefaultEmbed(
            title=_('Transfered succesfuly'),
            description=f'{ctx.author.mention} -> {member.mention} {amount} {coin}'
        )
        await ctx.send(embed=embed)
        

def setup(bot):
    bot.add_cog(EconomyCog(bot))
