import random
from typing import Union, Optional, List, Dict, Tuple, Set
from disnake import Member, User, Embed
from src.translation import get_translator
from src.ext.game.services.games.classes import Player
from .bunker_info import *

t = get_translator(route='ext.games')
BUNKER_STUFF_COUNT = 2


class BunkerData:
    """
    Data for game `Bunker`
    
    Attributes
    ----------
    * vote_started: :class:`bool`
        Flag for vote starting to prevent any actions before it ends.
    * hidden_data: :class:`Dict[Player, List[Tuple]]`
        Data which is shown for players that are not masters.
    * data: :class:`Dict[Player, Dict]`
        Actual data which is formed at start of the game (full shown for master).
    * event: :class:`Dict[]`
        Data about event including type, years etc.
    * voted: :class:`Set[Player]`
        Set of players that have already voted during the vote.
    * users_votes: :class:`Dict[Player, Optional[Player]]`
        Dictionary which stores players' votes during the vote.
    * players_to_exclude: :class:`Dict[Player, int]`
        Dictionary which stores potential candidates for excluding 
        and amount of votes against them.
    * event_embed: :class:`disnake.Embed`
        Embed with event info.
    * players_embed: :class:`Dict[Player, Embed]`
        All players' embeds in one dictionary.
    """
    def __init__(self) -> None:
        self.vote_started = False
        self.hidden_data: Dict[Player, List[Tuple]] = {}
        self.data: Dict[Player, Dict] = {}
        self.event: Dict = {}
        self.voted: Set[Player] = set()
        self.users_votes: Dict[Player, Optional[Player]] = {}
        self.players_to_exclude: Dict[Player, int] = {}

        self.event_embed: Embed = Embed()
        self.players_embeds: Dict[Player, Embed] = {}

    def create_game_data(self, player: Player, master: Player) -> None:
        data = self.data[player] = {
                'name': (random.choice(list(MaleNames)).value, random.choice(list(FemaleNames)).value),
                'age': random.randint(20, 90),
                'sex': random.choice(list(Sex)).value,
                'body_type': random.choice(list(BodyType)).value,
                'profession': random.choice(list(Professions)).value,
                'profession_quality': random.choice(list(Professionalism)).value,
                'hobby': random.choice(list(Hobby)).value,
                'hobby_quality': random.choice(list(Professionalism)).value,
                'phobia': random.choice(list(Phobias)).value,
                'character': self._get_rnd_characteristic(),
                'extra_info': random.choice(list(ExtraInfo)).value,
                'extra_stuff': random.choice(list(ExtraStuff)).value,
                'avatar': (random.choice(list(MaleThumbs)).value, random.choice(list(FemaleThumbs)).value)
            }
        
        self.hidden_data[player] = [
            ('Имя', data['name'][0] if data['sex'] == Sex.MALE.value else data['name'][1]),
            ('Аватар', data['avatar'][0] if data['sex'] == Sex.MALE.value else data['avatar'][1]),
        ]

        if not self.event_embed:
            self.event_embed = self._create_event_embed(master.player_id)
            
        self.players_embeds[player] = self.create_player_embed(self.make_data_fields(player))

    def _create_event_embed(self, master_id: int) -> Embed:
        cataclism = random.choice(list(Cataclisms)).value
        embed = Embed(
            title=t('game_event_card'),
            color = cataclism.COLOR.value
        )
        data = [
            ("", f'**Ведущий** - <@{master_id}>'),
            (cataclism.NAME.value, cataclism.DESC.value),
            ('Катакомбы', 'Единственный шанс, чтобы выжить в случае катаклизма - это попасть в бункер. У вас есть данные о спальных комнатах и запасной одежде.\n\n**Так же вам известно:**'),
            ('Время нахождения', f"Вам предстоит находиться в бункере {t('bunker_years', count=random.randint(1, 10))}"),
            ('Количество продовольствий', f"Еды в убежище хватит на {t('bunker_years', count=random.randint(1, 10))}"),
            ('В бункере имеется', ', '.join(item for item in [stuff.value for stuff in random.sample(list(BunkerStuff), BUNKER_STUFF_COUNT)]))
        ]

        for name, value in data:
            embed.add_field(name=name, value=value, inline=False)

        embed.set_image(url=cataclism.PHOTO.value)
        return embed
    
    def create_player_embed(self, fields: List[Tuple[str, str]]) -> Embed:
        embed = Embed(
            title=t('game_player_card'),
            color = 0x7B68EE
        )
        for name, value in fields[:-1]: 
            embed.add_field(name=name, value=value, inline=False)

        embed.set_thumbnail(url=fields[-1][-1])
        return embed

    def make_data_fields(self, player: Player) -> list[tuple[str, str]]:
        player_data = self.data[player]
        return [
                ('Имя', player_data['name'][0] if player_data['sex'] == Sex.MALE.value else player_data['name'][1]),
                ('Пол и возраст', f"{player_data['sex']}, {t('bunker_years', count=player_data['age'])}"),
                ('Телосложение', player_data['body_type']),
                ('Профессия', f"{player_data['profession']} на уровне: *{player_data['profession_quality']}*"),
                ('Хобби', f"{player_data['hobby']} на уровне: *{player_data['hobby_quality']}*"),
                ('Фобия', player_data['phobia']),
                ('Доп. информация', player_data['extra_info']),
                ('Инвентарь', player_data['extra_stuff']),
                ('Характеристика', player_data['character']),
                ('Аватар', player_data['avatar'][0] if player_data['sex'] == Sex.MALE.value else player_data['avatar'][1]),
            ]

    def clear_vote_data(self) -> None:
        self.users_votes.clear()
        self.players_to_exclude.clear()
    
    def _get_rnd_characteristic(self) -> str:
        subclass = random.choice(list(Character)).value
        characteristic = random.choice(list(subclass)).value
        return characteristic