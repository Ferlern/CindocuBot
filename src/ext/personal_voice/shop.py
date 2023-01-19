from abc import ABC, abstractmethod

import disnake
from src.database.models import EconomySettings, PersonalVoice

from src.translation import get_translator
from src.custom_errors import UsedNotOnGuild, MaxBitrateReached, MaxSlotsAmount
from src.discord_views.embeds import DefaultEmbed
from src.ext.economy.services import change_balance
from src.ext.economy.shops.base import Shop
from src.ext.personal_voice.services import (create_voice_channel,
                                             has_voice_channel,
                                             get_voice_channel)


t = get_translator(route="ext.personal_voice")
MAX_SLOTS_AMOUNT = 15
BITRATE = {
    64: 96,
    96: 128,
    128: 192,
    192: 256,
    256: 384
}


class VoiceShop(Shop):
    def __init__(self, author: disnake.Member, settings: EconomySettings) -> None:
        self._stratagy: VoiceShopStratagy
        self._settings = settings
        super().__init__(author, settings, timeout=300)
        self._update_stratagy()
        self.add_item(self._stratagy.build_select(settings))

    def create_embed(self) -> disnake.Embed:
        return self._stratagy.build_embed(self.author, self._settings)

    def is_empty(self) -> bool:
        return False

    @property
    def name(self) -> str:
        return t('voice_shop_name')

    async def update(self, message: disnake.Message) -> None:
        self._update_stratagy()
        await self._update_message(message)

    async def _response(self, inter: disnake.ApplicationCommandInteraction) -> None:
        await inter.response.send_message(
            embed=self.create_embed(),
            view=self,
        )

    def _update_stratagy(self) -> None:
        author = self.author
        if has_voice_channel(
            author.id,
            author.guild.id,
        ):
            self._stratagy = UpgradeVoiceStratagy()
        else:
            self._stratagy = NoVoiceStratagy()

    async def _update_message(self, message: disnake.Message) -> None:
        select = self._stratagy.build_select(self._settings)
        select._view = self  # noqa
        self.children[0] = select
        await message.edit(
            embed=self.create_embed(),
            view=self,
        )


class VoiceShopStratagy(ABC):
    @abstractmethod
    def build_embed(
        self,
        author: disnake.Member,
        settings: EconomySettings,
    ) -> disnake.Embed:
        return DefaultEmbed(
            title=t('voice_shop'),
            description=t('voice_shop_desc'),
        )

    @abstractmethod
    def build_select(self, settings: EconomySettings) -> disnake.ui.Select:
        pass


class NoVoiceStratagy(VoiceShopStratagy):
    def build_embed(
        self,
        author: disnake.Member,
        settings: EconomySettings,
    ) -> disnake.Embed:
        embed = super().build_embed(author, settings)
        embed.add_field(
            name='1. ' + t('voice_shop_voice_title'),
            value=t('voice_shop_voice_desc',
                    category_id=settings.voice_category_id,
                    price=settings.voice_price,
                    coin=settings.coin),
        )
        return embed

    def build_select(self, settings: EconomySettings) -> disnake.ui.Select:
        return BuyVoiceSelect(settings)


class UpgradeVoiceStratagy(VoiceShopStratagy):
    def build_embed(
        self,
        author: disnake.Member,
        settings: EconomySettings,
    ) -> disnake.Embed:
        embed = super().build_embed(author, settings)
        guild = author.guild

        if not guild:
            raise UsedNotOnGuild()

        voice_channel = get_voice_channel(
            author.id,
            guild.id,
        )
        embed.add_field(
            name='1. ' + t('voice_slots'),
            value=_get_slot_desc(
                voice_channel.slots,
                settings,
            )
        )
        embed.add_field(
            name='2. ' + t('voice_bitrate'),
            value=_get_bitrate_desc(
                voice_channel.max_bitrate,
                settings,
            )
        )
        return embed

    def build_select(self, settings: EconomySettings) -> disnake.ui.Select:
        return UpgradeVoiceSelect(settings)


class BuyVoiceSelect(disnake.ui.Select):
    view: VoiceShop

    def __init__(self, settings: EconomySettings) -> None:
        self._settings = settings
        options = [
            disnake.SelectOption(
                label=t('voice_shop_voice_title'),
            )
        ]
        super().__init__(options=options)

    async def callback(self, interaction: disnake.MessageInteraction, /) -> None:
        guild = interaction.guild
        author = interaction.author
        if not guild or not isinstance(author, disnake.Member):
            raise UsedNotOnGuild()

        if has_voice_channel(author.id, guild.id):
            await interaction.response.send_message(
                t('voice_already_exist'),
                ephemeral=True,
            )
            return

        settings = self._settings

        category = guild.get_channel(
            settings.voice_category_id,  # type: ignore
        )

        if not category or not isinstance(category, disnake.CategoryChannel):
            await interaction.response.send_message(
                t('voice_categoty_missing'),
                ephemeral=True,
            )
            return

        change_balance(
            guild_id=guild.id,
            user_id=author.id,
            amount=-settings.voice_price
        )

        voice = await category.create_voice_channel(
            name=author.name,
            user_limit=5,
        )
        await voice.set_permissions(
            author,
            manage_permissions=True,
            manage_channels=True
        )
        create_voice_channel(
            author.id,
            guild.id,
            voice_id=voice.id,
        )
        await interaction.response.send_message(
            t('voice_created'),
            ephemeral=True,
        )
        await self.view.update(interaction.message)


class UpgradeVoiceSelect(disnake.ui.Select):
    view: VoiceShop

    def __init__(self, settings: EconomySettings) -> None:
        self._settings = settings
        options = [
            disnake.SelectOption(
                label=t('voice_slots'),
                value='slot'
            ),
            disnake.SelectOption(
                label=t('voice_bitrate'),
                value='bitrate'
            ),
        ]
        super().__init__(options=options)

    async def callback(self, interaction: disnake.MessageInteraction, /) -> None:
        if not interaction.values:
            return  # impossible

        guild = interaction.guild
        if not guild:
            raise UsedNotOnGuild
        author_id = interaction.author.id
        guild_id = guild.id

        voice = get_voice_channel(
            author_id,
            guild_id,
        )
        settings = self._settings

        selected = interaction.values[0]
        handlers = {
            'slot': _buy_slot,
            'bitrate': _buy_bitrate
        }
        response_text = handlers[selected](
            user_id=author_id,
            guild_id=guild_id,
            voice=voice,
            settings=settings,
        )
        await interaction.response.send_message(
            response_text,
            ephemeral=True,
        )
        await self.view.update(interaction.message)


def _get_next_bitrate(bitrate: int) -> int:
    try:
        return BITRATE[bitrate]
    except KeyError as exc:
        raise MaxBitrateReached(t('voice_max_bitrate_reached')) from exc


def _get_next_slot(slot: int) -> int:
    if slot >= MAX_SLOTS_AMOUNT:
        raise MaxSlotsAmount(t('voice_max_slot_reached'))
    return slot + 1


def _count_next_bitrate_price(bitrate: int, price: int) -> int:
    next_bitrate = _get_next_bitrate(bitrate)
    return (next_bitrate - bitrate) * price // 32


def _count_next_slot_price(current_slot: int, price: int) -> int:
    return _get_next_slot(current_slot) * price


def _get_bitrate_desc(bitrate: int, settings: EconomySettings) -> str:
    try:
        return t(
            'voice_bitrate_desc',
            current=bitrate,
            next=_get_next_bitrate(
                bitrate,
            ),
            price=_count_next_bitrate_price(
                bitrate,
                settings.bitrate_price,
            ),
            coin=settings.coin
        )
    except MaxBitrateReached:
        return t('max')


def _get_slot_desc(slot: int, settings: EconomySettings) -> str:
    try:
        return t(
            'voice_slots_desc',
            current=slot,
            next=slot + 1,
            price=_count_next_slot_price(
                slot,
                settings.slot_price,
            ),
            coin=settings.coin,
        )
    except MaxSlotsAmount:
        return t('max')


def _buy_slot(
    user_id: int,
    guild_id: int,
    voice: PersonalVoice,
    settings: EconomySettings
) -> str:
    if voice.slots >= MAX_SLOTS_AMOUNT:
        raise MaxSlotsAmount()
    change_balance(
        user_id=user_id,
        guild_id=guild_id,
        amount=-_count_next_slot_price(
            voice.slots,
            settings.slot_price,
        )
    )
    voice.slots += 1
    voice.save()
    return t('voice_slots_purchased')


def _buy_bitrate(
    user_id: int,
    guild_id: int,
    voice: PersonalVoice,
    settings: EconomySettings
) -> str:
    change_balance(
        user_id=user_id,
        guild_id=guild_id,
        amount=-_count_next_bitrate_price(
            voice.max_bitrate,
            settings.bitrate_price,
        )
    )
    voice.max_bitrate = _get_next_bitrate(voice.max_bitrate)
    voice.save()
    return t('voice_bitrate_purchased')
