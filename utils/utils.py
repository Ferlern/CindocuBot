import discord


class DefaultEmbed(discord.Embed):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.color = 0x93a5cd


class DiscordTable:
    """Cteate 40-max-length table-like code block"""
    def __init__(self, **kwargs) -> None:
        """Cteate 40-max-length table-like code block
        
        kwargs
        --------
        columns `(list[str])`: 
        list of column names.
        
        max_columns_length `(list[int])`: 
        list of maximum length per columns.
        if the information in the column (or even the name of this column)
        is longer than the specified value, it will be truncated to max-2, ".." will be added.
        
        values `(list[list[str]])`: 
        one list for one row in table. 
        """
        self.columns = kwargs['columns']
        self.max_columns_length = kwargs['max_columns_length']
        self.values = kwargs['values']
        assert len(self.columns) == len(self.max_columns_length) == len(
            self.values[0]), "Table **kwargs must be equal length."
        assert sum(self.max_columns_length) <= 40 - len(
            self.columns), "Table length can't be more than 40"

    def __len__(self):
        return sum(self.max_columns_length)

    def __str__(self):
        string: str = ""
        string += " ".join([
            column_name + " " *
            (self.max_columns_length[index] - len(column_name))
            if len(column_name) <= self.max_columns_length[index] else
            column_name[:self.max_columns_length[index] - 2] + ".."
            for index, column_name in enumerate(self.columns)
        ])
        string += "\n"
        string += " ".join(
            ["―" * max_length for max_length in self.max_columns_length])
        for values in self.values:
            string += "\n"
            string += " ".join([
                value + " " * (self.max_columns_length[index] - len(value))
                if len(value) <= self.max_columns_length[index] else
                value[:self.max_columns_length[index] - 2] + ".."
                for index, value in enumerate(values)
            ])
        return string


class TimeConstans:
    second = 1
    minute = second * 60
    hour = minute * 60
    six_hour = hour * 6
    day = hour * 24
    week = day * 7
    mounts = day * 30


intervals = (
    ('days', TimeConstans.day),
    ('hours', TimeConstans.hour),
    ('minutes', TimeConstans.minute),
    ('seconds', TimeConstans.second),
)


def display_time(seconds, granularity=3, full=False):
    if seconds == 0:
        return '0'
    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            if full:
                result.append("**{}** {}".format(value, name))
            else:
                result.append("**{}**{}".format(value, name[:1]))
    return ' '.join(result[:granularity])

def experience_converting(current_exp: int):
    """Return tuple(level, gained_after_lvl_up, left_before_lvl_up)"""
    a1 = 100
    q = 1.1
    current_lvl = 0
    Sn = 100
    prevSn = 0
    while Sn <= current_exp:
        prevSn = Sn
        Sn = int(a1 * (q**(current_lvl + 2) - 1) / (q - 1))
        current_lvl += 1

    need_for_lvl_up = Sn - prevSn
    gained_after_lvl_up = current_exp - prevSn
    return (current_lvl, gained_after_lvl_up, need_for_lvl_up)

next_bitrate = {'64': 96, '96': 128, '128': 192, '192': 256, '256': 384}
