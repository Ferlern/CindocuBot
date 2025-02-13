from functools import cache
from typing import Optional, Union
import disnake
from disnake.ext import commands

from src.discord_views.paginate.paginators import ItemsPaginator
from src.converters import interacted_member
from src.bot import SEBot
from src.ext.members.services import get_member
from src.ext.actions.actions import get_resctictable_action
from src.translation import get_translator


t = get_translator(route='ext.restriction')


class RestrictionCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot

    @commands.slash_command()
    async def restrict(  # pylint: disable=too-many-arguments
        self,
        inter: disnake.GuildCommandInteraction,
        member: Optional[disnake.Member] = commands.Param(converter=interacted_member, default=None),
        role: Optional[disnake.Role] = commands.Param(default=None),
        action: str = commands.Param(
            choices=get_resctictable_action(),  # type: ignore
        ),
        decision=commands.Param(default='restrict', choices={
            t('allow'): 'allow',
            t('restrict'): 'restrict',
        })
    ) -> None:
        """
        Запретить другим учаcтникам выполнять с вами действия

        Parameters
        ----------
        member: Участник, для которого вы хотите запретить действие
        role: Роль, для которой вы хотите запретить действие
        action: Действие, которое вы хотите запретить
        decision: Запретить/Разрешить действие. Запрещает по умолчанию
        """
        if member is None and role is None:
            await inter.response.send_message(t('no_target_selected'), ephemeral=True)
            return

        decision = decision == 'allow'
        guild = inter.guild
        author = inter.author
        member_data = get_member(guild.id, author.id)
        restrictions = member_data.restrictions
        for restricted_object in [obj for obj in [member, role] if obj is not None]:
            string_id = str(restricted_object.id)
            obj_restrictions = restrictions.get(string_id, [])
            change_restrictions_for_object(obj_restrictions, action, decision)
            if obj_restrictions:
                restrictions[string_id] = obj_restrictions
            else:
                if string_id in restrictions:
                    del restrictions[string_id]

        member_data.save()
        await inter.response.send_message(t('updated'), ephemeral=True)

    @commands.slash_command()
    async def restrictions(
        self,
        inter: disnake.GuildCommandInteraction,
    ) -> None:
        """
        Показать выданные вами запреты
        """
        author = inter.author
        restrictions = get_member(inter.guild.id, author.id).restrictions
        inversed_actions = get_inversed_resctictable_action()

        if not restrictions:
            await inter.response.send_message(t('no_restrictions'), ephemeral=True)
            return

        actual_restrictions = []
        for obj_id, restrictions in restrictions.items():
            translated_restrictions = []
            for restrict in restrictions:
                translated = inversed_actions.get(restrict)
                if translated:
                    translated_restrictions.append(translated)
            if not translated_restrictions:
                continue

            obj_id = int(obj_id)
            member = inter.guild.get_member(obj_id)
            role = inter.guild.get_role(obj_id)
            obj = member or role
            if obj is None:
                continue
            obj_name = f'{obj} | `{obj.id}`'
            actual_restrictions.append(
                f'{obj_name} — {", ".join(translated_restrictions)}'
            )

        if not actual_restrictions:
            await inter.response.send_message(t('no_restrictions'), ephemeral=True)
            return

        view = RestrictionsPaginator(actual_restrictions, 10)
        await view.start_from(inter)


class RestrictionsPaginator(ItemsPaginator[str]):
    def create_embed(self) -> disnake.Embed:
        embed = disnake.Embed(
            title=t('restricted_actions'),
            description='\n'.join(self.items)
        )
        return embed

    async def page_callback(
        self,
        interaction: Union[disnake.ModalInteraction, disnake.MessageInteraction]
    ) -> None:
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def _response(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if self.max_page == 1:
            self.stop()
            await inter.response.send_message(embed=self.create_embed(), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.create_embed(), view=self, ephemeral=True)


@cache
def get_inversed_resctictable_action() -> dict[str, str]:
    return {v: k for k, v in get_resctictable_action().items()}


def change_restrictions_for_object(
    restrictions: list[str],
    action: str,
    decision: bool,
) -> None:
    if not decision:
        restrictions.append(action)
    else:
        if action in restrictions:
            restrictions.remove(action)


def setup(bot) -> None:
    bot.add_cog(RestrictionCog(bot))
