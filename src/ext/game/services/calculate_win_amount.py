def calculate_win_amount(
    number_of_winners: int,
    number_of_players: int,
    bet: int,
) -> int:
    if number_of_winners > number_of_players:
        raise ValueError("Number of players can't be lower than number of winners")
    pool = number_of_players * bet
    win_amount = pool // number_of_winners
    return win_amount
