import disnake
from typing import Optional
import datetime

from src.bot import SEBot
from src.logger import get_logger
from src.translation import get_translator
from src.discord_views.embeds import DefaultEmbed
from src.ext.pets.classes import Lobby
from src.ext.game.utils import user_to_player
from src.ext.pets.views.journal_paginator import JournalPaginator
from src.ext.pets.views.game import PetsGameView
from src.ext.pets.services import (get_main_pet,
        return_energy, accept_consume_energy)
from src.database.models import Pets


logger = get_logger()
t = get_translator(route='ext.pet_battle')


LOADING_GIF = "https://media1.tenor.com/m/HQ_1LH5VzRUAAAAd/discord-loading.gif"

 
class LobbyView(disnake.ui.View):
    def __init__(
        self,
        bot: SEBot,
        game_channel: disnake.TextChannel,
        lobby: Lobby
    ) -> None:
        self.bot = bot
        self.game_channel = game_channel
        self.lobby = lobby
        super().__init__(timeout=300)
        self.lobby_message: Optional[disnake.Message] = None

        self.creator_pet: Pets

        self.add_item(JoinButton())

    async def on_timeout(self) -> None:
        lobby_message = self.lobby_message

        if not lobby_message:
            return
        
        self.lobby.undo_lobby_created()
        return_energy(self.creator_pet.id)
        for item in self.children:
            item.disabled = True # type: ignore
        
        await lobby_message.edit(
            embed = DefaultEmbed(
                title=t("wait_for_players"),
                description=t("timeout")),
            view=self
        )
        await lobby_message.delete(delay=15)
    
    def create_embed(self, interaction: disnake.MessageInteraction) -> disnake.Embed:
        self.creator_pet = get_main_pet(interaction.guild.id, interaction.user.id) # type: ignore
        pet = self.creator_pet
        
        desc = t("wait_desc",
              user=interaction.user.mention,
              pet_name=pet.name,
              pet_level=pet.level) 

        return DefaultEmbed(
            title=t("wait_for_players"),
            description = desc
        )
    
    async def create_lobby(self, interaction) -> None:
        self.lobby_message = await self.game_channel.send(
            embed = self.create_embed(interaction),
            view = self
        )
    
    def create_prepare_embed(self) -> disnake.Embed:
        embed = DefaultEmbed(
            title=t('prepare_title'),
            description=t('prepare_desc')
        )
        embed.set_thumbnail(LOADING_GIF)
        return embed

    async def prepare(self) -> None:
        lobby_message = self.lobby_message
        if not lobby_message:
            return
        
        self.clear_items()
        await lobby_message.edit(
            embed=self.create_prepare_embed(),
            view=self
        )
        await lobby_message.delete(delay=5)
        self.lobby_message = None


class JoinButton(disnake.ui.Button):
    view: LobbyView

    def __init__(self) -> None:
        super().__init__(
            label = t("join_btn"),
            style=disnake.ButtonStyle.green
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        view = self.view
        lobby = view.lobby
        player = user_to_player(interaction.user)

        if player == lobby.creator:
            await interaction.response.send_message(t("lobby_creator_err"), ephemeral=True)
            return
        
        if lobby.full:
            await interaction.response.send_message(t("lobby_full_err"), ephemeral=True)
            return
        
        if not (pet := get_main_pet(lobby.guild.id, player.player_id)):
            await interaction.response.send_message(
                t("no_main_pet_err"),
                ephemeral=True
            )
            return
        
        if pet.spec == 'demon':
            await interaction.response.send_message(
                t("custom_pet_err"),
                ephemeral=True
            )
            return
        
        if pet.health <= 0 or view.creator_pet.health <= 0:
            await interaction.response.send_message(
                t("zero_health_pet_err"),
                ephemeral=True
            )
            return
        
        if abs(pet.level - view.creator_pet.level) > 5:
            await interaction.response.send_message(
                t("level_difference_err"),
                ephemeral=True
            )
            return
        
        consumed = accept_consume_energy(pet.id)
        if not consumed:
            await interaction.response.send_message(
                t("not_enough_energy_err"),
                ephemeral=True
            )
            return

        lobby.add(player)
        await self._start()
        await self._create_game()

    async def _create_game(self):
        view = self.view
        lobby = view.lobby

        members_to_ping = lobby.members_to_ping or []
        creator, player = (member.name for member in members_to_ping)

        thread = await self._create_thread(creator, player)
        journal = JournalPaginator(view.bot, thread)
        game_view = PetsGameView(view.bot, lobby.game, thread, journal)
        await self._mention_members(thread, members_to_ping)
        await self._start_game(journal, game_view, lobby)

    async def _create_thread(
        self,
        creator: str,
        player: str
    ) -> disnake.Thread:
        return await self.view.game_channel.create_thread(
            name=(f"{creator} vs {player} " +
                  f"{datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}"),
            type=disnake.ChannelType.private_thread,
            invitable=True,
            auto_archive_duration=60
        )
    
    async def _start_game(
        self, journal, game_view, lobby
    ) -> None:
        await journal.start_from()
        await lobby.start_game()
        await game_view.start_from()

    async def _mention_members(
        self, thread, members_to_ping
    ) -> None:
        await thread.send(
            ' '.join([member.mention for member in members_to_ping])
        )

    async def _start(self) -> None:
        view = self.view

        view.lobby.undo_lobby_created()
        await view.prepare()
