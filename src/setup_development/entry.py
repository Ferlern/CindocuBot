from __future__ import annotations
from functools import partial
from typing import Callable, TypeVar, TYPE_CHECKING
import peewee
import disnake
from disnake import Guild, utils as d_utils

from src.database.models import ChannelExperienceSettings
from src.ext.activity.services import get_experience_settings
from src.ext.suggestions.services import get_suggestion_settings
from src.ext.economy.services import get_economy_settings, add_shop_role
from src.ext.premoderation.services import get_premoderation_settings
from src.ext.members.services import get_welcome_settings, get_member
from src.ext.up_listener.services import get_reminder_settings
from src.ext.game.db_services import get_game_channel_settings
from src.ext.up_listener.up_reminder import MONITORING_INFORMATION
from src.logger import get_logger
from src.database.create import recreate_tables
from src.custom_errors import BadProjectSettings
if TYPE_CHECKING:
    from src.bot import SEBot


T = TypeVar('T')
logger = get_logger()
LVL_ROLE_NAME_TEMPLATE = 'lvl_{lvl}_role'
LVL_ROLES = [3, 5, 7, 10]
PERSONAL_VOICE_CATEGORY_NAME = 'private voices'
DEFAULT_MONEY_AMOUNT = 100000
DEFAULT_CRYSTALS_AMOUNT = 10000
EXPERIENCE_CATEGOTY_NAME = 'experience channels'
EXPERIENCE_CHANNELS_TEMPLATES = [
    {
        'name': 'low_exp_channel',
        'channel': ChannelExperienceSettings(
            min_experience_per_message=1,
            max_experience_per_message=2,
            cooldown=0,
            minimal_message_length=0,
        )
    },
    {
        'name': 'hight_exp_channel',
        'channel': ChannelExperienceSettings(
            min_experience_per_message=60,
            max_experience_per_message=60,
            cooldown=0,
            minimal_message_length=0,
        )
    },
]
SUGGESTION_CHANNEL_NAME = 'suggestions'
SHOP_ROLE_NAME_TEMPLATE = 'shop_role_{price}'
SHOP_ROLES_PRICES = [100, 500, 1000, 5000]
PREMODERATION_CHANNEL_NAME = 'content_premoderation'
WELCOME_CHANNEL_NAME = 'welcome_channel'
WELCOME_TITLE = 'Hello user!'
WELCOME_TEXT = 'A new user has joined: %{member}!'
REMINDER_CHANNEL_NAME = 'up_reminders'
TESTER_ROLE_NAME = 'Developer'
GAME_CATEGORY_NAME = 'game category'
VOICE_GAME_CATEGORY_NAME = 'voice game category'
GAMES = ['bunker_game']


async def setup_development(  # noqa
    bot: SEBot,
    app_name: str,
    testers_ids: list[int],
    test_guilds_ids: list[int],
    create_new_test_guild: bool,
    recreate_database_schema: bool,
    prepare_database: bool,
    prepare_guilds: bool,
) -> None:
    print("\n"*3)
    print("="*60)
    logger.info(
        "Application is in test/development mode.\n"
        "Test guilds and database will be updated now, this may take some time"
    )
    print("="*60)
    test_guilds = await check_and_convert_test_constans(
        bot, app_name, test_guilds_ids[:], testers_ids, create_new_test_guild
    )

    logger.info("The following guilds will be used for testing:\n%s",
                "\n".join(guild.name for guild in test_guilds))

    if prepare_guilds is True and prepare_database is False:
        raise BadProjectSettings("Can't prepare guilds without preparing database")
    if recreate_database_schema:
        logger.info("Recreating database...")
        recreate_tables()
    logger.info("Links to guilds for testing:")
    await send_links_to_test_guild(test_guilds)
    if prepare_guilds:
        logger.info("preparing test guilds...")
        await setup_guilds(test_guilds)
    if prepare_database:
        logger.info("preparing database...")
        await setup_default_data(test_guilds, testers_ids)
    if prepare_guilds:
        logger.info("Grant admin role to testers...")
        await grant_admin_to_testers(test_guilds, testers_ids)


async def grant_admin_to_testers(
    test_guilds: list[disnake.Guild],
    testers_ids: list[int]
) -> None:
    for guild in test_guilds:
        create_method = partial(
            guild.create_role,
            permissions=disnake.Permissions(administrator=True),
        )
        admin_role = await get_or_create_by_name(
            guild.roles, create_method, name=TESTER_ROLE_NAME
        )
        for user_id in testers_ids:
            member = guild.get_member(user_id)
            if member is not None:
                await member.add_roles(admin_role)


async def setup_default_data(
    test_guilds: list[disnake.Guild],
    testers_ids: list[int]
) -> None:
    for guild in test_guilds:
        for user_id in testers_ids:
            member_data = get_member(guild.id, user_id)
            member_data.balance = DEFAULT_MONEY_AMOUNT
            member_data.donate_balance = DEFAULT_CRYSTALS_AMOUNT
            member_data.save()


async def setup_guilds(
    test_guilds: list[disnake.Guild],
) -> None:
    for guild in test_guilds:
        logger.info("preparing %s...", guild.name)
        await ensure_experience_settings(guild)
        await ensure_suggestion_settings(guild)
        await ensure_economy_settings(guild)
        await ensure_shop_roles(guild)
        await ensure_premoderation_settings(guild)
        await ensure_welcome_settings(guild)
        await ensure_reminder_settings(guild)
        await ensure_game_channel_settings(guild)


async def ensure_reminder_settings(guild: Guild) -> None:
    channel = await get_or_create_by_name(
        guild.channels, guild.create_text_channel, name=REMINDER_CHANNEL_NAME
    )
    for bot_id in MONITORING_INFORMATION:
        settings = get_reminder_settings(guild.id, bot_id)
        if settings.channel_id != channel.id:
            settings.channel_id = channel.id
            settings.save()


async def ensure_welcome_settings(guild: Guild) -> None:
    settings = get_welcome_settings(guild.id)
    channel = await get_or_create_by_name(
        guild.channels, guild.create_text_channel, name=WELCOME_CHANNEL_NAME
    )
    settings.channel_id = channel.id
    settings.text = WELCOME_TEXT
    settings.title_text = WELCOME_TITLE
    settings.save()


async def ensure_premoderation_settings(guild: Guild) -> None:
    settings = get_premoderation_settings(guild.id)
    channel = await get_or_create_by_name(
        guild.channels, guild.create_text_channel, name=PREMODERATION_CHANNEL_NAME
    )
    settings.premoderation_channels = [channel.id]
    settings.save()


async def ensure_shop_roles(guild: Guild) -> None:
    for price in SHOP_ROLES_PRICES:
        name = SHOP_ROLE_NAME_TEMPLATE.format(price=price)
        role = await get_or_create_by_name(
            guild.roles, guild.create_role, name=name
        )
        try:
            add_shop_role(guild.id, role.id, price)
        except peewee.IntegrityError:
            pass


async def ensure_economy_settings(guild: Guild) -> None:
    settings = get_economy_settings(guild.id)
    category = await get_or_create_by_name(
        guild.channels, guild.create_category, name=PERSONAL_VOICE_CATEGORY_NAME
    )
    if settings.voice_category_id != category.id:
        settings.voice_category_id = category.id
        settings.save()


async def ensure_suggestion_settings(guild: Guild) -> None:
    settings = get_suggestion_settings(guild.id)
    channel = await get_or_create_by_name(
        guild.channels, guild.create_text_channel, name=SUGGESTION_CHANNEL_NAME
    )
    if settings.suggestions_channel != channel.id:
        settings.suggestions_channel = channel.id
        settings.save()


async def ensure_game_channel_settings(guild: Guild) -> None:
    settings = get_game_channel_settings(guild.id)
    
    game_cat = await get_or_create_by_name(
        guild.categories, guild.create_category, name=GAME_CATEGORY_NAME
    )
    if settings.category_id != game_cat.id:
        settings.category_id = game_cat.id

    voice_game_cat = await get_or_create_by_name(
        guild.categories, guild.create_category, name=VOICE_GAME_CATEGORY_NAME
    )
    if settings.voice_game_category_id != voice_game_cat.id:
        settings.voice_game_category_id = voice_game_cat.id

    channels = {}
    messages = {}
    for game in GAMES:
        channel = await get_or_create_by_name(
            game_cat.channels, game_cat.create_text_channel, name=game
        )
        channels[game] = channel.id
    settings.channels_id = channels
    settings.messages_id = messages

    settings.save()


async def ensure_experience_settings(guild: Guild) -> None:
    settings = get_experience_settings(guild.id)

    exp_cat = await get_or_create_by_name(
        guild.channels, guild.create_category, EXPERIENCE_CATEGOTY_NAME
    )
    channels = {}
    for template in EXPERIENCE_CHANNELS_TEMPLATES:
        name = template['name']
        channel_settings = template['channel']
        channel = await get_or_create_by_name(
            exp_cat.channels, exp_cat.create_text_channel, name=name  # type: ignore
        )
        channels[str(channel.id)] = channel_settings
    settings.experience_channels = channels

    roles = {}
    for lvl_role in LVL_ROLES:
        name = LVL_ROLE_NAME_TEMPLATE.format(lvl=lvl_role)
        role = await get_or_create_by_name(
            guild.roles, guild.create_role, name=name
        )
        roles[str(lvl_role)] = role.id
    settings.roles = roles

    settings.save()


async def get_or_create_by_name(
    iterable: list[T],
    create_method: Callable,
    name: str
) -> T:
    obj = d_utils.get(iterable, name=name)
    if not obj:
        obj = await create_method(name=name)
    return obj


async def send_links_to_test_guild(test_guilds: list[disnake.Guild]) -> None:
    for guild in test_guilds:
        invites = await guild.invites()

        if len(invites) == 0:
            invites.append(await create_invite(guild))

        logger.info('Invite for guild %s: %s', guild.name, invites[0].url)


async def create_invite(guild: disnake.Guild) -> disnake.Invite:
    text_channels = [ch for ch in guild.channels if isinstance(ch, disnake.TextChannel)]
    if len(text_channels) == 0:
        text_channels.append(await guild.create_text_channel(name='invite'))

    channel = text_channels[0]
    return await channel.create_invite()


async def check_guilds(
    bot: SEBot,
    app_name: str,
    guilds_ids: list[int],
    create_new_test_guild: bool,
) -> None:
    if len(guilds_ids) > 0:
        for id_ in guilds_ids:
            if bot.get_guild(id_) is None:
                raise BadProjectSettings(
                    f"Guild with id {id_} is listed as a test guild, but the bot doesn't see it"
                )
        return

    # if no guild provided try to find created one
    test_guild = d_utils.get(bot.guilds, name=app_name)
    if test_guild is not None:
        guilds_ids.append(test_guild.id)
        return

    if create_new_test_guild is False:
        raise BadProjectSettings(
            "The test guild is not specified, has not been created and cannot "
            "be created according to the specified settings"
        )

    # create new one
    try:
        test_guild = await bot.create_guild(name=app_name)
    except disnake.HTTPException as error:
        raise BadProjectSettings(
            "Guild for tests is not specified, and creating a new one caused an error. "
            "Create a guild yourself, invite a bot and specify "
            "ID of this guild in settings.py") from error
    guilds_ids.append(test_guild.id)


async def check_and_convert_test_constans(
    bot: SEBot,
    app_name: str,
    test_guilds_ids: list[int],
    testers_ids: list[int],
    create_new_test_guild: bool,
) -> list[disnake.Guild]:
    if len(testers_ids) == 0:
        raise BadProjectSettings("Specify the discord ID of at least one tester in settings.py")

    await check_guilds(bot, app_name, test_guilds_ids, create_new_test_guild)
    test_guilds = [bot.get_guild(id_) for id_ in test_guilds_ids]
    test_guilds = [guild for guild in test_guilds if guild is not None]

    return test_guilds
