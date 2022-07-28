import logging
import time
from typing import Union

import discord
from utils.custom_errors import (AlreadyLiked, MaxBitrateReached,
                                 MaxSlotsAmount, NotEnoughMoney, NotMarried,
                                 TargetAlreadyMarried, UserAlreadyMarried,
                                 VoiceAlreadyCreated, BonusAlreadyReceived)
from utils.utils import experience_converting, next_bitrate

from .data_controller.models import (Likes, PersonalVoice, Relationship,
                                     UserInfo, UserRoles)

loger = logging.getLogger('Arctic')


class MemberDataController:
    model = UserInfo

    def __init__(self, id):
        self.user_info, created = UserInfo.get_or_create(id=id)
        self.user_info: UserInfo
        self.to_save = []
        if created:
            loger.debug(f'user {self.user_info.id} created')
        else:
            loger.debug(f'user {self.user_info.id} getted')

    def take_bonus(self, amount: int):
        current_day = time.time() // 86400
        
        if self.user_info.bonus_taked_on_day < current_day:
            self.user_info.bonus_taked_on_day = current_day
            self.change_balance(amount)
        else:
            raise BonusAlreadyReceived
        
    
    def change_balance(self, amount: int):
        self.user_info.balance += amount

        if self.user_info.balance < 0:
            raise NotEnoughMoney(f'{abs(self.user_info.balance)}')

    def set_mute_time(self, mute_time: int):
        """Sets mute time relative to the current time

        Args:
            mute_time (int): mute durations (in seconds)
        """
        end_time = time.time() + mute_time
        self.user_info.mute_end_at = end_time

    def end_mute(self):
        self.user_info.mute_end_at = None

    def warn(self):
        self.user_info.warn += 1

    def unwarn(self):
        if self.user_info.warn > 0:
            self.user_info.warn -= 1

    def create_private_voice(self, voice_id):
        if self.user_info.user_personal_voice:
            raise VoiceAlreadyCreated
        PersonalVoice.create(user=self.user_info.id,
                              voice_id=voice_id,
                              slots=5,
                              max_bitrate=64)

    def buy_slot(self, price):
        voice = PersonalVoice.get(user=self.user_info.id)
        if voice.slots >= 25:
            raise MaxSlotsAmount
        price = voice.slots * price
        self.change_balance(-price)
        self.save()

        voice.slots += 1
        voice.save()

    def buy_bitrate(self, price):
        voice = PersonalVoice.get(user=self.user_info.id)
        try:
            add_bitrate = next_bitrate[str(
                voice.max_bitrate)] - voice.max_bitrate
        except KeyError:
            raise MaxBitrateReached
        price = add_bitrate / 32 * price
        self.change_balance(-price)
        self.save()

        voice.max_bitrate += add_bitrate
        voice.save()

    def marry(self, pair_id):
        if self._get_relationship():
            raise UserAlreadyMarried
        other = MemberDataController(id=pair_id)
        if other._get_relationship():
            raise TargetAlreadyMarried
        relationship = Relationship(soul_mate=other.user_info.id,
                                    user=self.user_info.id,
                                    married_time=time.time())
        self.to_save.append(relationship)

    def divorce(self, confirmed=False):
        relationsip = self._get_relationship(raw=True)
        if not relationsip: raise NotMarried
        if confirmed:
            relationsip.delete_instance()

    def like(self, to_member: discord.Member):
        self._change_like(to_member, 1)

    def dislike(self, to_member: discord.Member):
        self._change_like(to_member, -1)

    def reset_like(self, to_member: discord.Member):
        self._change_like(to_member, 0)

    def save(self):
        self.user_info.save()
        loger.debug(f'user {self.user_info.id} saved')
        for to_save in self.to_save:
            to_save.save()

    @property
    def balance(self) -> int:
        return self.user_info.balance

    @property
    def roles(self) -> list[int]:
        roles = self.user_info.user_roles.dicts().execute()
        roles = [role['role_id'] for role in roles]
        return roles

    @property
    def level(self) -> tuple[int]:
        """Return tuple(level, gained_after_lvl_up, left_before_lvl_up)"""
        current_exp = self.user_info.experience
        return experience_converting(current_exp)

    @property
    def likes(self) -> int:
        like = Likes.select().where(Likes.to_user == self.user_info.id,
                                    Likes.type == 1).count()
        dislike = Likes.select().where(Likes.to_user == self.user_info.id,
                                       Likes.type == -1).count()
        return like - dislike

    @property
    def soul_mate(self) -> int:
        relationship = self._get_relationship()
        if not relationship:
            return None
        else:
            return relationship['user'] if relationship[
                'user'] != self.user_info.id else relationship['soul_mate']

    @property
    def married_time(self) -> int:
        relationship = self._get_relationship()
        if not relationship:
            return None
        else:
            return relationship['married_time']

    def _get_relationship(self, raw=False) -> Union[dict, Relationship]:
        relationship = Relationship.select().where(
            (Relationship.user == self.user_info.id)
            | (Relationship.soul_mate == self.user_info.id))
        if not relationship:
            return None

        if raw:
            return relationship[0]
        else:
            return relationship.dicts().execute()[0]

    def _change_like(self, to_member: discord.Member, type: bool):
        to_member_id = to_member.id
        MemberDataController(to_member_id)
        like, created = Likes.get_or_create(user=self.user_info.id,
                                            to_user=to_member_id)
        if like.type == type:
            raise AlreadyLiked
        if type == 0:
            like.delete_instance()
            return
        like.type = type
        like.save()
