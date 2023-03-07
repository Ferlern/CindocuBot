from typing import Sequence

from src.database.models import GameStatistics, psql_db


@psql_db.atomic()
def count_wins(guild_id: int, user_ids: Sequence[int], money_won: int) -> None:
    for user_id in user_ids:
        statistic, _ = GameStatistics.get_or_create(guild=guild_id, user=user_id)
        statistic.wins += 1
        statistic.money_won += money_won
        statistic.save()
