from peewee import *

conn = SqliteDatabase("./core_elements/data_controller/data.db")


class BaseModel(Model):
    class Meta:
        database = conn


class UserInfo(BaseModel):
    id = AutoField(column_name='id')
    balance = IntegerField(column_name='balance', default=0)
    experience = IntegerField(column_name='experience', default=0)
    voice_activity = IntegerField(column_name='voice_activity', default=0)
    biography = TextField(column_name='biography', null=True)
    mute_end_at = IntegerField(column_name='mute_end_at', null=True)
    warn = IntegerField(column_name='warn', default=0)
    on_server = BooleanField(column_name='on_server', default=True)

    class Meta:
        table_name = 'user'


class PersonalVoice(BaseModel):
    id = AutoField(column_name='id')
    user = ForeignKeyField(UserInfo,
                           column_name='user',
                           backref="user_personal_voice")
    voice_id = IntegerField(column_name='voice_id')
    slots = IntegerField(column_name='slots')
    max_bitrate = IntegerField(column_name='max_bitrate')

    class Meta:
        table_name = 'user_personal_voice'


class UserRoles(BaseModel):
    id = AutoField(column_name='id')
    user = ForeignKeyField(UserInfo, column_name='user', backref="user_roles")
    role_id = IntegerField(column_name='role_id')

    class Meta:
        table_name = 'user_roles'


class Relationship(BaseModel):
    id = AutoField(column_name='id')
    user = ForeignKeyField(UserInfo,
                           column_name='user',
                           backref="relationship")
    soul_mate = ForeignKeyField(UserInfo,
                                column_name='soul_mate',
                                backref="relationship")
    married_time = IntegerField(column_name='married_time')

    class Meta:
        table_name = 'relationship'


class Likes(BaseModel):
    id = AutoField(column_name='id')
    user = ForeignKeyField(UserInfo, column_name='user', backref="likes")
    to_user = IntegerField(column_name='to_user')
    type = IntegerField(column_name='type', null=True)

    class Meta:
        table_name = 'likes'


class ModLog(BaseModel):
    id = AutoField(column_name='id')
    moderator = IntegerField(column_name='moderator')
    action = TextField(column_name='action')
    reason = TextField(column_name='reason')
    duration = IntegerField(column_name='duration', null=True)
    creation_time = IntegerField(column_name='creation_time')

    class Meta:
        table_name = 'mod_log'


class ModLogTarget(BaseModel):
    id = AutoField(column_name='id')
    mod_log = ForeignKeyField(ModLog,
                              column_name='mod_log',
                              backref="mod_log_target")
    target = IntegerField(column_name='target')
    
    class Meta:
        table_name = 'mod_log_target'


class ShopRoles(BaseModel):
    id = AutoField(column_name='id')
    role_id = IntegerField(column_name='role_id')
    price = IntegerField(column_name='price')

    class Meta:
        table_name = 'shop_roles'


class Suggestions(BaseModel):
    message_id = PrimaryKeyField(column_name='message_id')
    text = TextField(column_name='text')
    url = TextField(column_name='url', null=True)
    author = IntegerField(column_name='author')

    class Meta:
        table_name = 'suggestions'


class Codes(BaseModel):
    id = PrimaryKeyField(column_name='id')
    code = TextField(column_name='code')
    name = TextField(column_name='name', null=True)
    group = IntegerField(column_name='group', null=True)

    class Meta:
        table_name = 'codes'


def close_connection():
    conn.close()