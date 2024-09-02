import disnake
from .actions import Actions
from src.translation import get_translator

t = get_translator(route='ext.pet_battle')

class Journal(disnake.Embed):
    def __init__(self) -> None:
        self._actions: list[str] = []
        self._max_lines_per_page = 15
        super().__init__(
            title = t('game_journal'),
            color = 0xFF7F24
        )
        self.update()

    @property
    def full(self) -> bool:
        return len(self._actions) >= self._max_lines_per_page
    
    def update(self) -> disnake.Embed:
        self.description = (
            "```xl\n" +
            "\n".join(self._actions) +
            "```"
        )
        return self
    
    def add(self, action: Actions, **kwargs) -> None:
        self._actions.append(action.get_translated(**kwargs))
        self.update()