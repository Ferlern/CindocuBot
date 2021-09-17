import operator
import time
from functools import reduce

from peewee import *

from core_elements.data_controller.models import Mod_log, Mod_log_target


class Logs:
    @classmethod
    def create_mod_log(cls,
                       moderator,
                       action,
                       reason="not specified",
                       duration=None,
                       targets=[]) -> None:
        """Create log for mod. action

        Args:
            moderator (discord.User)
            action (str)
            reason (str, optional). Defaults to "not specified".
            duration (int, optional). Defaults to None.
            targets (list[discord.User], optional). Defaults to [].
        """
        moderator_id = moderator.id
        assert action in [
            'mute', 'warn', 'ban', 'banid', 'unmute', 'unwarn', 'unban',
            'clear'
        ], f'incorrect action {action}'
        Mod_log.create(moderator=moderator_id,
                       action=action,
                       reason=reason,
                       duration=duration,
                       creation_time=time.time())
        log_id = Mod_log.select(fn.MAX(Mod_log.id)).scalar()

        data = [{'mod_log': log_id, 'target': target.id} for target in targets]
        Mod_log_target.insert_many(data).execute()

    @classmethod
    def get_mod_logs(cls, **filters):
        """Receives all logs that have passed the filter

        filters:
        --------
            period: `int` (seconds)
            action: `str`
            moderator: `discord.User`
        """

        period = filters.get('period')
        action = filters.get('action')
        moderator = filters.get('moderator')

        if action:
            assert action in [
                'mute', 'warn', 'ban', 'banid', 'unmute', 'unwarn', 'unban',
                'clear'
            ], f'incorrect action {action}'

        expression_list = []
        if period:
            creation_time = time.time() - period
            expression_list.append(
                getattr(Mod_log, 'creation_time') > creation_time)
        if action:
            expression_list.append(getattr(Mod_log, 'action') == action)
        if moderator:
            expression_list.append(
                getattr(Mod_log, 'moderator') == moderator.id)
        if expression_list:
            anded_expr = reduce(operator.and_, expression_list)
            return Mod_log.select().where(anded_expr).order_by(
                Mod_log.id.desc()).dicts().execute()
        else:
            return Mod_log.select().order_by(
                Mod_log.id.desc()).dicts().execute()

    @classmethod
    def get_mod_log(cls, id: int):
        return Mod_log.get(id=id)

    @classmethod
    def get_mod_log_targets(cls, id: int):
        return Mod_log_target.select().where(
            Mod_log_target.mod_log == id).dicts().execute()
