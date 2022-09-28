import datetime
from typing import Sequence
from peewee import (Model, BigAutoField,
                    ForeignKeyField, CharField, SQL)
from playhouse.postgres_ext import (PostgresqlExtDatabase, BigIntegerField,
                                    IntegerField, AutoField, ArrayField,
                                    JSONField, TextField, CompositeKey,
                                    DateTimeField)

from src.settings import DATABASE

psql_db = PostgresqlExtDatabase(DATABASE['dbname'],
                                host=DATABASE['host'],
                                port=DATABASE['port'],
                                user=DATABASE['user'],
                                password=DATABASE['password'])


class BaseModel(Model):
    """Base model for connection"""

    class Meta:  # pylint: disable=too-few-public-methods
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
    id = BigAutoField(primary_key=True)
    locale = CharField(max_length=10, constraints=[
                       SQL("DEFAULT 'ru'")], default='ru')
    prefixes = ArrayField(TextField, null=True)  # type: ignore #TODO <- idk
    commands_channels = ArrayField(BigIntegerField, null=True)


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
    guild_id = ForeignKeyField(Guilds, primary_key=True, on_delete='CASCADE')
    suggestions_channel = BigIntegerField(null=True)


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
    guild_id = ForeignKeyField(Guilds, primary_key=True, on_delete='CASCADE')
    marry_price = IntegerField(constraints=[SQL("DEFAULT 1000")], default=1000)


class ModerationSettings(BaseModel):
    """
    Model for moderation ext settings

    Attributes
    ----------
    id: :class:`int`
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
    guild_id = ForeignKeyField(Guilds, primary_key=True, on_delete='CASCADE')
    warns_system = JSONField(null=True)
    moderators_roles = ArrayField(BigIntegerField, null=True)
    mute_role = BigIntegerField(null=True)


class EconomySettings(BaseModel):
    """
    Model for economy ext settings

    Attributes
    ----------
    id: :class:`int`
        Guild ID.
    coin: :class:`str`
        Coin emoji or text.
    daily: :class:`int`
        Amount of coins in the daily command.
    voice_category_id: :class:`int`
        Category where personal voices will be created
    voice_price: :class:`int`
        Personal voice price
    slot_price: :class:`int`
        Personal voice slot price
    bitrate_price: :class:`int`
        Personal voice bitrate price
    """
    guild_id = ForeignKeyField(Guilds, primary_key=True, on_delete='CASCADE')
    coin = CharField(max_length=30, constraints=[
                     SQL("DEFAULT ':coin:'")], default=':coin:')
    daily = IntegerField(constraints=[SQL("DEFAULT 35")], default=35)
    voice_category_id = BigIntegerField(null=True)
    voice_price = IntegerField(constraints=[SQL("DEFAULT 2000")],
                               default=2000)
    slot_price = IntegerField(constraints=[SQL("DEFAULT 100")], default=100)
    bitrate_price = IntegerField(constraints=[SQL("DEFAULT 100")],
                                 default=100)


class ExperienceSettings(BaseModel):
    """
    Model for experience ext settings

    Attributes
    ----------
    id: :class:`int`
        Guild ID.
    experience_channels: Optional[:class:`list[int]`]
        IDs of the channels where experience will be availible
    cooldown: Optional[:class:`int`]
        minimal time in seconds between two counted message
    minimal_message_length: Optional[:class:`int`]
        minimal length of the counted messages
    min_experience_per_message: Optional[:class:`int`]
        experience will be randomly given started from this value
    max_experience_per_message: Optional[:class:`int`]
        experience will be randomly given but not more than this value
    roles: Optional[:class:`dict[str, int]`]
        dict that containe roles for experience system.
        keys coinaines level that user should reach for get role
        values coinaines id of the target role
    """
    guild_id = ForeignKeyField(Guilds, primary_key=True, on_delete='CASCADE')
    experience_channels = ArrayField(BigIntegerField, null=True)
    cooldown = IntegerField(null=True)
    minimal_message_length = IntegerField(null=True)
    min_experience_per_message = IntegerField(
        constraints=[SQL('DEFAULT 1')],
        default=1,
    )
    max_experience_per_message = IntegerField(
        constraints=[SQL('DEFAULT 1')],
        default=1,
    )
    coins_per_level_up = IntegerField(
        constraints=[SQL('DEFAULT 10')],
        default=10,
    )
    roles = JSONField(null=True)


class Users(BaseModel):
    """
    Model for discord users

    Attributes
    ----------
    id: :class:`int`
        User ID.
    """
    id = BigAutoField(primary_key=True)


class Members(BaseModel):
    """
    Model for guild members

    Attributes
    ----------
    balance: :class:`int`
        Balance for economy exts.
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
    """
    user_id = ForeignKeyField(Users, on_delete='CASCADE')
    guild_id = ForeignKeyField(Guilds, on_delete='CASCADE')
    balance = IntegerField(constraints=[SQL('DEFAULT 0')], default=0)
    experience = IntegerField(constraints=[SQL('DEFAULT 0')], default=0)
    voice_activity = IntegerField(constraints=[SQL('DEFAULT 0')], default=0)
    biography = CharField(column_name='biography', max_length=300, null=True)
    bonus_taked_on_day = IntegerField(
        constraints=[SQL('DEFAULT 0')], default=0)
    mute_end_at = IntegerField(null=True)
    warns = IntegerField(constraints=[SQL('DEFAULT 0')], default=0)

    class Meta:  # pylint: disable=too-few-public-methods
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
    user_id = ForeignKeyField(Users, on_delete='CASCADE')
    guild_id = ForeignKeyField(Guilds, on_delete='CASCADE')
    role_id = BigIntegerField()

    class Meta:  # pylint: disable=too-few-public-methods
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
    voice_id: :class:`int`
        Voice guild channel ID.
    slots: :class:`int`
        Max amount of slots in the voice channel.
    max_bitrate: :class:`int`
        Max bitrate of the voice channel.
    """
    user_id = ForeignKeyField(Users, on_delete='CASCADE')
    guild_id = ForeignKeyField(Guilds, on_delete='CASCADE')
    voice_id = BigIntegerField()
    slots = IntegerField(constraints=[SQL('DEFAULT 5')], default=5)
    max_bitrate = IntegerField(constraints=[SQL('DEFAULT 64')], default=64)

    class Meta:  # pylint: disable=too-few-public-methods
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
    user_id = ForeignKeyField(Users, on_delete='CASCADE')
    to_user_id = ForeignKeyField(Users, on_delete='CASCADE')
    guild_id = ForeignKeyField(Guilds, on_delete='CASCADE')
    type = IntegerField(constraints=[SQL('DEFAULT 0')], default=0)

    class Meta:  # pylint: disable=too-few-public-methods
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
    id = AutoField()
    guild_id = ForeignKeyField(Guilds, on_delete='CASCADE')
    creation_time = IntegerField()
    participants: Sequence['RelationshipParticipant']


class RelationshipParticipant(BaseModel):
    """
    Model for members who stays in relationships

    relationship_id: :class:`int`
        relationships group ID.
    user_id: :class:`int`
        User ID.
    """
    relationship_id = ForeignKeyField(
        Relationships,
        backref='participants',
        on_delete='CASCADE',
    )
    user_id = ForeignKeyField(Users, on_delete='CASCADE')

    class Meta:  # pylint: disable=too-few-public-methods
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
    guild_id = ForeignKeyField(Guilds, on_delete='CASCADE')
    role_id = BigIntegerField()
    price = IntegerField()

    class Meta:  # pylint: disable=too-few-public-methods
        primary_key = CompositeKey('guild_id', 'role_id')


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
    message_id = BigAutoField()
    guild_id = ForeignKeyField(Guilds, on_delete='CASCADE')
    channel_id = BigIntegerField()
    author = ForeignKeyField(Users, on_delete='CASCADE')
    text = CharField(max_length=4000)
    url = CharField(max_length=255, null=True)


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
    id = AutoField(column_name='id')
    guild_id = ForeignKeyField(Guilds, on_delete='CASCADE')
    user_id = ForeignKeyField(Users, on_delete='CASCADE')
    creation_time = DateTimeField(default=datetime.datetime.now)
    action_name = CharField()
    description = CharField(max_length=65535)


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
    url: Optional[:class:`str`]
        link to the attchment
    """
    guild_id = ForeignKeyField(Guilds, on_delete='CASCADE')
    channel_id = BigIntegerField()
    author = ForeignKeyField(Users, on_delete='CASCADE')
    url = CharField(max_length=255, null=True)


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
    guild_id = ForeignKeyField(Guilds, on_delete='CASCADE')
    premoderation_channels = ArrayField(BigIntegerField, null=True)


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
    guild_id = ForeignKeyField(Guilds, on_delete='CASCADE')
    channel_id = BigIntegerField(null=True)
    title_text = CharField(null=True)
    text = CharField(max_length=2000, null=True)


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
    name = CharField(max_length=50, primary_key=True)  # TODO that doesn't work
    code = CharField(max_length=65535)
    group = IntegerField(null=True)


psql_db.connect()
