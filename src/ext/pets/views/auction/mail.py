from typing import Optional, Union
import disnake
from datetime import datetime

from src.bot import SEBot
from src.discord_views.paginate.peewee_paginator import PeeweePaginator
from src.discord_views.embeds import DefaultEmbed
from src.database.models import AuctionMail
from src.translation import get_translator
from src.ext.pets.services import make_read


t = get_translator(route='ext.pets')


class MailView(PeeweePaginator[AuctionMail]):
    def __init__(
        self,
        bot: SEBot,
        guild: disnake.Guild,
        user: disnake.User | disnake.Member
    ) -> None:
        self.bot = bot
        self.guild = guild
        self.user = user
        super().__init__(
            AuctionMail,
            items_per_page=10,
            filters={
                'guild': AuctionMail.guild == self.guild.id,
                'user': AuctionMail.user == self.user.id
            }, # type: ignore
            order_by=AuctionMail.is_read.asc() # type: ignore
        )
        self.current_mail: Optional[AuctionMail] = None
        mail_select = MailSelect()

        self.add_item(mail_select)
        
        self._updateable_components = [mail_select]
        self._mail_items = []

        self._update_components()

    async def _response(
        self,
        inter: disnake.ApplicationCommandInteraction
    ) -> None:
        self._update_components()

        await inter.response.defer()
        await inter.followup.send(
            embed=self.create_embed(),
            view=self
        )

    async def page_callback(
        self,
        interaction: Union[
            disnake.ModalInteraction,
            disnake.MessageInteraction
        ],
    ) -> None:
        self.current_mail = None
        self._update_components()

        await interaction.response.defer()
        await interaction.edit_original_message(
            embed=self.create_embed(),
            view=self
        )

    def _update_components(self) -> None:
        for component in self._updateable_components:
            component.update()

    def create_embed(self) -> disnake.Embed:
        if not self.items:
            return DefaultEmbed(
                title=t("no_mails")
            )
        
        if not self.current_mail:
            return DefaultEmbed(
                title=t('mail_title'),
                description='\n'.join(
                    [f"{self.define_is_read_symbol(mail.is_read)}" +
                    f"{index+1}. <@{mail.buyer_id}> {t('bought_your_item')}"
                    for index, mail in enumerate(self.items, 0)])
                )        
        
        mail = self.current_mail
        desc = t(
            'mail_desc',
            user_id=mail.user.id,
            buy_date=disnake.utils.format_dt(mail.buy_date, 'f'),
            buyer_id=mail.buyer_id,
            proceed=mail.proceed 
        )

        return DefaultEmbed(
            title=t('mail_title'),
            description=desc
        )
    
    def _mail_buttons(self) -> None:
        if self._mail_items: return
        self.add_item(delete_mail_btn := DeleteMailButton())
        self.add_item(back_btn := BackButton())

        self._mail_items.append(delete_mail_btn)
        self._mail_items.append(back_btn)

    def _general_buttons(self) -> None:
        for item in self._mail_items:
            self.remove_item(item) 
        self._mail_items = []

    def define_is_read_symbol(self, is_read: bool) -> str:
        return {
            False: "◆ | ",
            True: "-# ◇ | "
        }[is_read]
    
    async def update_view(
        self,
        inter: disnake.MessageCommandInteraction,
        with_back: bool = False
    ) -> None:
        if with_back:
            self.update()
            self.current_mail = None
            self._general_buttons()
        self._update_components()
        await inter.response.edit_message(
            embed=self.create_embed(),
            view=self
        )
    
    
class MailSelect(disnake.ui.Select):
    view: MailView

    def __init__(self) -> None:
        super().__init__(
            placeholder=t("choose_mail"),
            row=2
        )

    def update(self) -> None:
        if not self.view.items:
            self.placeholder = t("no_mail_ph")
            self.disabled = True
            self.options = [disnake.SelectOption(label="...")]
            return
        
        options = [
            disnake.SelectOption(
                label=f"{index+1}. {self.define_is_read(mail.is_read)}",
                value=str(index)
            ) for index, mail in enumerate(self.view.items, 0)
        ]
        self.options = options

    def define_is_read(self, is_read: bool) -> str:
        return {
            False: t("not_read"),
            True: t("read")
        }[is_read]

    async def callback(
        self,
        interaction: disnake.MessageCommandInteraction
    ) -> None:
        view = self.view
        view.current_mail = (mail := view.items[int(self.values[0])])

        make_read(mail.id)

        view._mail_buttons()
        await view.update_view(interaction)

    
class DeleteMailButton(disnake.ui.Button):
    view: MailView

    def __init__(self) -> None:
        super().__init__(
            label=t("delete_mail_button"),
            style=disnake.ButtonStyle.red
        )

    async def callback(
        self,
        interaction: disnake.MessageCommandInteraction
    ) -> None:
        mail = self.view.current_mail
        if not mail: return

        mail.delete_by_id(mail.id)
        await self.view.update_view(interaction, with_back=True)


class BackButton(disnake.ui.Button):
    view: MailView

    def __init__(self) -> None:
        super().__init__(
            label=t("back_button"),
            style=disnake.ButtonStyle.gray
        )

    async def callback(
        self,
        interaction: disnake.MessageCommandInteraction
    ) -> None:
        await self.view.update_view(interaction, with_back=True)