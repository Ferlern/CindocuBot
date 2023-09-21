# type: ignore
# types are ignored because of bad Peewee type system

import datetime
from dataclasses import dataclass
from typing import Optional, Sequence, TypedDict
from peewee import (Model, BigAutoField,
                    ForeignKeyField, CharField, SQL, BooleanField)
from playhouse.postgres_ext import (PostgresqlExtDatabase, BigIntegerField,
                                    IntegerField, AutoField, ArrayField,
                                    JSONField, TextField, CompositeKey,
                                    DateTimeField, DateTimeTZField)

from src.settings import DATABASE

psql_db = PostgresqlExtDatabase(DATABASE['dbname'],
                                host=DATABASE['host'],
                                port=DATABASE['port'],
                                user=DATABASE['user'],
                                password=DATABASE['password'])


@dataclass
class RelationshipTopEntry:
    creation_time: int
    first_user_id: int
    second_user_id: int


class ChannelExperienceSettings(TypedDict):
    """
    Settings for channel where experience counts

    cooldown: Optional[:class:`int`]
        minimal time in seconds between two counted message
    minimal_message_length: Optional[:class:`int`]
        minimal length of the counted messages
    min_experience_per_message: Optional[:class:`int`]
        experience will be randomly given started from this value
    max_experience_per_message: Optional[:class:`int`]
        experience will be randomly given but not more than this value
    """
    min_experience_per_message: int
    max_experience_per_message: int
    cooldown: Optional[int] = None
    minimal_message_length: Optional[int] = None


class BaseModel(Model):
    """Base model for connection"""

    class Meta:
        database = psql_db


class Guilds(BaseModel):
    """
    Model for discord guilds & basic settings

    Attributes
    ----------
    id: :class:`int`
        Guild ID.
    locale: :class:`str`
        Guild languege.
    prefixes: Optional[:class:`list[str]`]
        Guild commands prefixes, will override default list.
    commands_channels: Optional[:class:`list[id]`]
        IDs of channels where `@everyone` can run prefix commands.
    """
    id: int = BigAutoField(primary_key=True)
    locale: str = CharField(max_length=10, constraints=[
        SQL("DEFAULT 'ru'")], default='ru')
    prefixes: Optional[list[str]] = ArrayField(TextField, null=True)
    commands_channels: Optional[list[int]] = ArrayField(BigIntegerField, null=True)


class SuggestionSettings(BaseModel):
    """
    Model for suggestion ext settings

    Attributes
    ----------
    id: :class:`int`
        Guild ID.
    suggestions_channel: Optional[:class:`int`]
        ID of the channel where suggestions will be posted.
    """
    guild_id: Guilds = ForeignKeyField(Guilds, primary_key=True, on_delete='CASCADE')
    suggestions_channel: Optional[int] = BigIntegerField(null=True)


class RelationshipsSettings(BaseModel):
    """
    Model for marry ext settings

    Attributes
    ----------
    id: :class:`int`
        Guild ID.
    marry_price: :class:`int`
        Price for create new realtionship.
    """
    guild_id: Guilds = ForeignKeyField(Guilds, primary_key=True, on_delete='CASCADE')
    marry_price: int = IntegerField(constraints=[SQL("DEFAULT 1000")], default=1000)


class ModerationSettings(BaseModel):
    """
    Model for moderation ext settings

    Attributes
    ----------
    guild_id: :class:`int`
        Guild ID.
    warns_system: Optional[:class:`dict`]
        settings for warn system. Each warn is an
        nested dict that contains:
        - `text` - text that will be sended
        into warned user DM.
        - `mute_time` - seconds of mute.
        - `ban` - bolean. Should be member banned or not.\n

    moderators_roles: Optional[:class:`list`]
        moderators roles id
    mute_role: Optional[:class:`int`]
        ID of the role that will be
        assigned to a muted member
    """
    guild_id: Guilds = ForeignKeyField(Guilds, primary_key=True, on_delete='CASCADE')
    warns_system: Optional[dict] = JSONField(null=True)
    moderators_roles: Optional[list[int]] = ArrayField(BigIntegerField, null=True)
    mute_role: Optional[int] = BigIntegerField(null=True)


class EconomySettings(BaseModel):
    """
    Model for economy ext settings

    Attributes
    ----------
    id: :class:`int`
        Guild ID.
    coin: :class:`str`
        Coin emoji or text.
    crystal: :class:`str`
        donate currency emoji or text.
    daily: :class:`int`
        Amount of coins in the daily command.
    voice_category_id: :class:`int`
        Category where personal voices will be created
    main_voice_id: :class:`int`
        Voice channel in the personal voice category
        used to create another voices
    voice_price: :class:`int`
        Personal voice price
    slot_price: :class:`int`
        Personal voice slot price
    bitrate_price: :class:`int`
        Personal voice bitrate price
    role_creation_price: :class:`int`
        Cost of creating role (second currency)
    role_day_tax: :class:`int`
        Tax on created role (second currency)
        If member does not have enough money, the role will be removed
    role_under_which_create_roles: :class:Optional[`int`]
        The role whose guild position will be used when creating new roles.
        They will be placed below it, if role specified
    """
    guild_id: Guilds = ForeignKeyField(Guilds, primary_key=True, on_delete='CASCADE')
    coin: str = CharField(max_length=255, constraints=[
        SQL("DEFAULT ':coin:'")], default=':coin:')
    crystal: str = CharField(max_length=255, constraints=[
        SQL("DEFAULT ':large_blue_diamond:'")], default=':large_blue_diamond:')
    daily: int = IntegerField(constraints=[SQL("DEFAULT 35")], default=35)
    voice_category_id: Optional[int] = BigIntegerField(null=True)
    main_voice_id: Optional[int] = BigIntegerField(null=True)
    voice_price: int = IntegerField(constraints=[SQL("DEFAULT 2000")],
                                    default=2000)
    slot_price: int = IntegerField(constraints=[SQL("DEFAULT 100")], default=100)
    bitrate_price: int = IntegerField(constraints=[SQL("DEFAULT 100")],
                                      default=100)
    role_creation_price: int = IntegerField(constraints=[SQL("DEFAULT 100")], default=100)
    role_day_tax: int = IntegerField(constraints=[SQL("DEFAULT 10")], default=10)
    role_under_which_create_roles: Optional[int] = BigIntegerField(null=True)


class ExperienceSettings(BaseModel):
    """
    Model for experience ext settings

    Attributes
    ----------
    id: :class:`int`
        Guild ID.
    experience_channels: Optional[:class:`Optional[dict[str, ChannelExperienceSettings]]`]
        Mapping channel ID to its experience settings
    coins_per_level_up: :class:`int`
        count reward = 100 + (this value) * (new_lvl)
    roles: Optional[:class:`dict[str, int]`]
        dict that containe roles for experience system.
        keys coinaines level that user should reach for get role
        values coinaines id of the target role
    """
    guild_id: Guilds = ForeignKeyField(Guilds, primary_key=True, on_delete='CASCADE')
    experience_channels: Optional[dict[str, ChannelExperienceSettings]] = JSONField(null=True)
    coins_per_level_up: int = IntegerField(
        constraints=[SQL('DEFAULT 10')],
        default=10,
    )
    roles: Optional[dict[str, int]] = JSONField(null=True)


class Users(BaseModel):
    """
    Model for discord users

    Attributes
    ----------
    id: :class:`int`
        User ID.
    """
    id: int = BigAutoField(primary_key=True)


class Members(BaseModel):
    """
    Model for guild members

    Attributes
    ----------
    on_guild: :class:`bool`
        Whether the user is currently on the guild.
        Can be outdated so use it only for data display purposes.
    balance: :class:`int`
        Balance for economy exts.
    donate_balance: :class:`int`
        Second balance. Currency received for real money
    experience: :class:`int`
        Points gained for text activity.
    voice_activity: :class:`int`
        Seconds in voice channel.
    biography: Optional[:class:`str`]
        Short bio, will be displayed in profile.
    bonus_taked_on_day: :class:`int`
        UNIX day when daily command used last time.
    mute_end_at: :class:`int`
        UNIX second when mute role should be removed.
    warns: :class:`int`
        Amount of member warns on guild.
    restrictions: :class:`Optional[dict[str, list[str]]]`
        Mapping discord user's id to restricted actions
        If action is restricred it cannot be used on this member
    game_ticket_until: :class:`Optional[datetime]`
        The time until which the user can play games
    """
    user_id: Users = ForeignKeyField(Users, on_delete='CASCADE')
    guild_id: Guilds = ForeignKeyField(Guilds, on_delete='CASCADE')
    on_guild: bool = BooleanField(SQL('DEFAULT TRUE'), default=True)
    balance: int = IntegerField(constraints=[SQL('DEFAULT 0')], default=0)
    donate_balance: int = IntegerField(constraints=[SQL('DEFAULT 0')], default=0)
    experience: int = IntegerField(constraints=[SQL('DEFAULT 0')], default=0)
    voice_activity: int = IntegerField(constraints=[SQL('DEFAULT 0')], default=0)
    biography: Optional[str] = CharField(column_name='biography', max_length=300, null=True)
    bonus_taked_on_day: int = IntegerField(
        constraints=[SQL('DEFAULT 0')], default=0)
    mute_end_at: Optional[int] = IntegerField(null=True)
    warns: int = IntegerField(constraints=[SQL('DEFAULT 0')], default=0)
    restrictions: dict[str, list[str]] = JSONField(
        default=dict,
        constraints=[SQL("DEFAULT '{}'::jsonb")],
    )
    game_ticket_until: Optional[datetime.datetime] = DateTimeField(null=True)

    class Meta:
        primary_key = CompositeKey('user_id', 'guild_id')


class UserRoles(BaseModel):
    """
    Model for member roles

    Attributes
    ----------
    user_id: :class:`int`
        User ID.
    guild_id: :class:`int`
        Guild ID.
    role_id: :class:`int`
        Role ID.
    """
    user_id: Users = ForeignKeyField(Users, on_delete='CASCADE')
    guild_id: Guilds = ForeignKeyField(Guilds, on_delete='CASCADE')
    role_id: int = BigIntegerField()

    class Meta:
        primary_key = False
        table_name = 'user_roles'


class PersonalVoice(BaseModel):
    """
    Model for members personal voice

    Attributes
    ----------
    user_id: :class:`int`
        User ID.
    guild_id: :class:`int`
        Guild ID.
    slots: :class:`int`
        Max amount of slots in the voice channel.
    max_bitrate: :class:`int`
        Max bitrate of the voice channel.
    voice_id: :class:`int`
        Last voice channel ID. Null if it has never been created
    current_name: :class:`str`
        Last voice name. Null if it has never been created
    current_slots: :class:`int`
        Current amount of slots in the voice channel.
    current_bitrate: :class:`int`
        Current bitrate of the voice channel.
    current_overwrites: :class:`dict`
        Current permission overwrites of the voice channel.
    """
    user_id: Users = ForeignKeyField(Users, on_delete='CASCADE')
    guild_id: Guilds = ForeignKeyField(Guilds, on_delete='CASCADE')
    slots: int = IntegerField(constraints=[SQL('DEFAULT 5')], default=5)
    max_bitrate: int = IntegerField(constraints=[SQL('DEFAULT 64')], default=64)

    voice_id: Optional[int] = BigIntegerField(null=True)
    current_name: Optional[str] = CharField(max_length=255, null=True)
    current_slots: int = IntegerField(constraints=[SQL('DEFAULT 5')], default=5)
    current_bitrate: int = IntegerField(constraints=[SQL('DEFAULT 64')], default=64)
    current_overwrites: Optional[dict[str, list[int]]] = JSONField(null=True)

    class Meta:
        primary_key = CompositeKey('user_id', 'guild_id')


class Likes(BaseModel):
    """
    Model for reputataion

    Attributes
    ----------
    user_id: :class:`int`
        ID of the user who likes.
    to_user_id: :class:`int`
        ID of the liked user.
    guild_id: :class:`int`
        Guild ID.
    type: `Literal[-1, 0, 1]`
        Like / dislake.
    """
    user_id: Users = ForeignKeyField(Users, on_delete='CASCADE')
    to_user_id: Users = ForeignKeyField(Users, on_delete='CASCADE')
    guild_id: Guilds = ForeignKeyField(Guilds, on_delete='CASCADE')
    type: int = IntegerField(constraints=[SQL('DEFAULT 0')], default=0)

    class Meta:
        primary_key = CompositeKey('user_id', 'guild_id', 'to_user_id')


class Relationships(BaseModel):
    """
    Model for relationship groups

    id: :class:`int`
        Relationships group ID.
    guild_id: :class:`int`
        Guild where relationship was created
    creation_time: :class:`int`
        UNIX seconds when group is created.
    """
    id: int = AutoField()
    guild_id: Guilds = ForeignKeyField(Guilds, on_delete='CASCADE')
    creation_time: int = IntegerField()
    participants: Sequence['RelationshipParticipant']


class RelationshipParticipant(BaseModel):
    """
    Model for members who stays in relationships

    relationship_id: :class:`int`
        relationships group ID.
    user_id: :class:`int`
        User ID.
    """
    relationship_id: Relationships = ForeignKeyField(
        Relationships,
        backref='participants',
        on_delete='CASCADE',
    )
    user_id: Users = ForeignKeyField(Users, on_delete='CASCADE')

    class Meta:
        primary_key = CompositeKey('relationship_id', 'user_id')


class ShopRoles(BaseModel):
    """
    Model for guild-shop roles

    Attributes
    ----------
    guild_id: :class:`int`
        Guild ID.
    role_id: :class:`int`
        Role ID.
    price: :class:`int`
        price of a role.
    """
    guild_id: Guilds = ForeignKeyField(Guilds, on_delete='CASCADE')
    role_id: int = BigIntegerField()
    price: int = IntegerField()

    class Meta:
        primary_key = CompositeKey('guild_id', 'role_id')


class CreatedShopRoles(BaseModel):
    """
    Model for created by members roles

    Attributes
    ----------
    guild: :class:`Guilds`
        Guild.
    creator: :class:`Users`
        Role creator.
    role_id: :class:`int`
        Role ID. Empty if role has not yet been approved
    approved: :class:`bool`
        Whether the role was approved by server moderation
    shown: :class:`bool`
        Whether the role will be shown in shop
    price: :class:`int`
        Role purchase price for other members
    properties: :class:`dict`
        Creator-selected role properties. Color, name ect.
    """
    guild: Guilds = ForeignKeyField(Guilds, on_delete='CASCADE')
    creator: Users = ForeignKeyField(Users, on_delete='CASCADE')
    role_id: Optional[int] = BigIntegerField(null=True)
    approved: bool = BooleanField(default=False)
    shown: bool = BooleanField(default=True)
    price: int = IntegerField(constraints=[SQL('DEFAULT 5000')], default=5000)
    properties: dict = JSONField()

    class Meta:
        primary_key = CompositeKey('guild', 'creator')


class RolesInventory(BaseModel):
    """
    Model for roles that members have bought

    Attributes
    ----------
    guild: :class:`Guilds`
        Guild.
    user: :class:`Users`
        User who bought role.
    role_id: :class:`int`
        Role ID.
    purchase_price: :class:`int`
        The amount of money spent on the purchase. May be differ from current role price
    """
    guild: Guilds = ForeignKeyField(Guilds, on_delete='CASCADE')
    user: Users = ForeignKeyField(Users, on_delete='CASCADE')
    role_id: int = BigIntegerField()
    purchase_price: int = IntegerField()

    class Meta:
        primary_key = CompositeKey('guild', 'user', 'role_id')


class Suggestions(BaseModel):
    """
    Model for guild's suggestions

    Attributes
    ----------
    message_id: :class:`int`
        ID of a message that containe suggestion
    guild_id: :class:`int`
        ID of guild where suggestion is created
    channel_id: :class:`int`
        ID of channel where suggestion was posted
    author: :class:`int`
        ID of a user who send suggestion
    text: :class:`str`
        suggestion content
    url: Optional[:class:`str`]
        link to the first attchment in suggestion message
    """
    message_id: int = BigAutoField()
    guild_id: Guilds = ForeignKeyField(Guilds, on_delete='CASCADE')
    channel_id: int = BigIntegerField()
    author: Users = ForeignKeyField(Users, on_delete='CASCADE')
    text: str = CharField(max_length=4000)
    url: Optional[str] = CharField(max_length=255, null=True)


class History(BaseModel):
    """
    Model for storing actions like balance changes,
    moderation actions, etc.

    id: :class:`int`
        Action ID.
    guild_id: :class:`int`
        Guild where action happened.
    user_id: :class:`int`
        ID. User who performed the action
    creation_time: :class:`int`
        When action is created.
    action_name: :class:`str`
        Short user friendly action identifier
    description: :class:`str`
        Long action description, should store all important information
    """
    id: int = AutoField(column_name='id')
    guild_id: Guilds = ForeignKeyField(Guilds, on_delete='CASCADE')
    user_id: Users = ForeignKeyField(Users, on_delete='CASCADE')
    creation_time: datetime.datetime = DateTimeField(default=datetime.datetime.now)
    action_name: str = CharField()
    description: str = CharField(max_length=65535)


class PremoderationItem(BaseModel):
    """
    Model for guild's suggestions

    Attributes
    ----------
    guild_id: :class:`int`
        ID of guild where content is sended
    channel_id: :class:`int`
        ID of channel where content should be posted
    author: :class:`int`
        ID of a user who send content
    content: :class:`str`
        Item content
    urls: list[:class:`str`]
        Link to the attchment
    """
    guild_id: Guilds = ForeignKeyField(Guilds, on_delete='CASCADE')
    channel_id: int = BigIntegerField()
    author: Users = ForeignKeyField(Users, on_delete='CASCADE')
    content: Optional[str] = CharField(max_length=65535, null=True)
    urls: Optional[list[str]] = ArrayField(TextField, null=True)


class PremoderationSettings(BaseModel):
    """
    Settings for premoderation ext

    Attributes
    ----------
    guild_id: :class:`int`
        Guild ID.
    premoderation_channels: Optional[:class:`list[id]`]
        IDs of channels where premoderation works.
    """
    guild_id: Guilds = ForeignKeyField(Guilds, on_delete='CASCADE')
    premoderation_channels: Optional[list[int]] = ArrayField(BigIntegerField, null=True)


class WelcomeSettings(BaseModel):
    """
    Settings for welcome ext

    Attributes
    ----------
    guild_id: :class:`int`
        Guild ID.
    channel_id: :class:`int`
        ID of channel where welcome message will be sended.
    title_text: Optional[:class:`str`]
        Title for welcome message embed
    text: Optional[:class:`str`]
        Description for welcome message embed
    """
    guild_id: Guilds = ForeignKeyField(Guilds, on_delete='CASCADE')
    channel_id: Optional[int] = BigIntegerField(null=True)
    title_text: Optional[str] = CharField(null=True)
    text: Optional[str] = CharField(max_length=2000, null=True)


class ReminderSettings(BaseModel):
    """
    Settings for each monitoring

    Attributes
    ----------
    guild_id: :class:`int`
        Guild ID.
    monitoring_bot_id: :class:`int`
        ID of bot that registers ups for monitoring
    channel_id: Optional[:class:`int`]
        ID of channel where remind message will be sended.
    text: Optional[:class:`str`]
        Reminder message text
    """
    guild_id: Guilds = ForeignKeyField(Guilds, on_delete='CASCADE')
    monitoring_bot_id: int = BigIntegerField()
    channel_id: Optional[int] = BigIntegerField(null=True)
    text: Optional[int] = CharField(max_length=2000, null=True)

    class Meta:
        primary_key = CompositeKey('guild_id', 'monitoring_bot_id')


class Reminders(BaseModel):
    """
    Current active reminders

    Attributes
    ----------
    guild_id: :class:`int`
        Guild ID.
    monitoring_bot_id: :class:`int`
        ID of bot that registers ups for monitoring
    send_time: :class:`datetime`
        Date when reminder should send message
    """
    guild_id: Guilds = ForeignKeyField(Guilds, on_delete='CASCADE')
    monitoring_bot_id: int = BigIntegerField()
    send_time: datetime.datetime = DateTimeTZField()


class GameStatistics(BaseModel):
    """
    Current active reminders

    Attributes
    ----------
    guild: :class:`Guilds`
        Guild.
    user: :class:`Users`
        User.
    wins: :class:`str`
        Number of games won
    money_won: :class:`int`
        Amount of money won
    """
    guild: Guilds = ForeignKeyField(Guilds, on_delete='CASCADE')
    user: Users = ForeignKeyField(Users, on_delete='CASCADE')
    wins: int = IntegerField(constraints=[SQL("DEFAULT 0")], default=0)
    money_won: int = BigIntegerField(constraints=[SQL("DEFAULT 0")], default=0)

    class Meta:
        primary_key = CompositeKey('guild', 'user')


class Puzzles(BaseModel):
    """
    Pazzles
    """
    id: int = BigAutoField()
    guild: Guilds = ForeignKeyField(Guilds, on_delete='CASCADE')
    text: str = CharField(max_length=2000)
    answers: list[str] = ArrayField(TextField)
    prize: int = IntegerField()


# Depricated?
class Codes(BaseModel):
    """
    Model for stored eval codes

    Attributes
    ----------
    name: :class:`str`
        TODO
    code: :class:`str`
        python snippet
    group: :class:`str`
        code groups; group can be executed atomary? TODO
    """
    name: str = CharField(max_length=50, primary_key=True)  # TODO that doesn't work
    code: str = CharField(max_length=65535)
    group: Optional[int] = IntegerField(null=True)


psql_db.connect()
