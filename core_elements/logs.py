import operator
import time
from functools import reduce

from peewee import *

from core_elements.data_controller.models import ModLog, ModLogTarget


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
            moderator (disnake.User)
            action (str)
            reason (str, optional). Defaults to "not specified".
            duration (int, optional). Defaults to None.
            targets (list[disnake.User], optional). Defaults to [].
        """
        moderator_id = moderator.id
        assert action in [
            'mute', 'warn', 'ban', 'banid', 'unmute', 'unwarn', 'unban',
            'clear'
        ], f'incorrect action {action}'
        ModLog.create(moderator=moderator_id,
                       action=action,
                       reason=reason,
                       duration=duration,
                       creation_time=time.time())
        log_id = ModLog.select(fn.MAX(ModLog.id)).scalar()

        data = [{'mod_log': log_id, 'target': target.id} for target in targets]
        ModLogTarget.insert_many(data).execute()

    @classmethod
    def get_mod_logs(cls, **filters):
        """Receives all logs that have passed the filter

        filters:
        --------
            period: `int` (seconds)
            action: `str`
            moderator: `disnake.User`
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
                getattr(ModLog, 'creation_time') > creation_time)
        if action:
            expression_list.append(getattr(ModLog, 'action') == action)
        if moderator:
            expression_list.append(
                getattr(ModLog, 'moderator') == moderator.id)
        if expression_list:
            anded_expr = reduce(operator.and_, expression_list)
            return ModLog.select().where(anded_expr).order_by(
                ModLog.id.desc())
        else:
            return ModLog.select().order_by(
                ModLog.id.desc())

    @classmethod
    def get_mod_log(cls, id: int):
        return ModLog.get_or_none(id=id)

    @classmethod
    def get_mod_log_targets(cls, id: int):
        return ModLogTarget.select().where(
            ModLogTarget.mod_log == id).dicts().execute()
