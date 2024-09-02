from __future__ import annotations
from typing import TYPE_CHECKING
import disnake

from src.logger import get_logger
from src.translation import get_translator
from src.ext.pets.classes import PetsGame
from src.ext.game.utils import user_to_player
from src.ext.pets.utils import GameEmbed
from src.ext.pets.classes import Skill

if TYPE_CHECKING:
    from .game import PetsGameView

logger = get_logger()
t = get_translator(route='ext.pet_battle')


class SkillUseView(disnake.ui.View):
    def __init__(self,
        game: PetsGame,
        user: disnake.Member | disnake.User,
        game_view: PetsGameView,
        skills: list[Skill]
    ) -> None:
        super().__init__(timeout=180)
        self.user = user
        self.game = game
        self.game_view = game_view
        self.skills = skills

        self.skills_map = {
            skill.id: skill.skill_showcase()
            for skill in self.skills
        }
        self._current_skill_id: str

        self._select_items()

    def _create_embed(self) -> disnake.Embed:
        desc = self._create_embed_desc()
        embed = GameEmbed(
            title = t("skills"),
            description = desc
        )
        return embed
    
    def _create_embed_desc(self) -> str:
        return t("choose_skill")
    
    def _select_items(self) -> None:
        self.clear_items()
        self.add_item(SkillSelect(self.skills_map))

    def _use_items(self) -> None:
        self.clear_items()
        self.add_item(UseSkillButton())
        self.add_item(BackButton())
    
    async def update_view(
        self,
        interaction: disnake.MessageInteraction
    ) -> None:
        self.clear_items()
        await interaction.response.edit_message(
            embed=self._create_embed(),
            view=self
        )

    async def start_from(
        self,
        interaction: disnake.MessageInteraction
    ):
        await interaction.response.send_message(
            embed=self._create_embed(),
            view=self,
            ephemeral=True
        )
    

class SkillSelect(disnake.ui.Select):
    view: SkillUseView

    def __init__(self, skills_map):
        options = [
            disnake.SelectOption(
                label=t(name),
                value=name
            ) for name in skills_map
        ]
        super().__init__(options=options)

    async def callback(
        self,
        interaction: disnake.MessageInteraction
    ) -> None:
        name = self.values[0]
        self.view._current_skill_id = name  
        self.view._use_items()
        await interaction.response.edit_message(
            embed=self.view.skills_map[name],
            view=self.view
        )


class UseSkillButton(disnake.ui.Button):
    view: SkillUseView

    def __init__(self) -> None:
        super().__init__(
            label=t("use_skill_btn"),
            style=disnake.ButtonStyle.green
        )

    async def callback(
        self,
        interaction: disnake.MessageInteraction
    ) -> None:
        view = self.view
        if not view.game.is_your_turn(user_to_player(interaction.user)):
            await interaction.response.send_message(
                t("not_your_turn"), ephemeral=True)
            return

        accepted = await view.game.accept_use_skill(
            skill_id=view._current_skill_id,
            player=user_to_player(interaction.user)
        )
        if not accepted:
            await interaction.response.send_message(
                content=t("skill_on_cooldown"),
                ephemeral=True
            )
            return
        
        await self.view.update_view(interaction)
        await self.view.game_view.update_view()


class BackButton(disnake.ui.Button):
    view: SkillUseView

    def __init__(self) -> None:
        super().__init__(
            label=t("back_btn"),
            style=disnake.ButtonStyle.gray
        )

    async def callback(
        self,
        interaction: disnake.MessageInteraction
    ) -> None:
        self.view._select_items()
        await interaction.response.edit_message(
            embed=self.view._create_embed(),
            view=self.view
        )