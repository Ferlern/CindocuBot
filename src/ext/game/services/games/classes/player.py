from dataclasses import dataclass


@dataclass(frozen=True)
class Player:
    player_id: int
    bot: bool
