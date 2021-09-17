import logging
import time
from typing import Union

import discord
from utils.custom_errors import (AlreadyLiked, MaxBitrateReached,
                                 MaxSlotsAmount, NotEnoughMoney, NotMarried,
                                 TargetAlreadyMarried, UserAlreadyMarried,
                                 VoiceAlreadyCreated)

from .data_controller.models import (Likes, Personal_voice, Relationship,
                                     User_info, User_roles)

loger = logging.getLogger('Arctic')

next_bitrate = {'64': 96, '96': 128, '128': 192, '192': 256, '256': 384}


class Member_data_controller:
    model = User_info

    def __init__(self, id):
        self.user_info, created = User_info.get_or_create(id=id)
        self.user_info: User_info
        self.to_save = []
        if created:
            loger.debug(f'user {self.user_info.id} created')
        else:
            loger.debug(f'user {self.user_info.id} getted')

    def change_balance(self, amount: int):
        self.user_info.balance += amount

        if self.user_info.balance < 0:
            raise NotEnoughMoney(f'{abs(self.user_info.balance + amount)}')

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
        Personal_voice.create(user=self.user_info.id,
                              voice_id=voice_id,
                              slots=5,
                              max_bitrate=64)

    def buy_slot(self, price):
        voice = Personal_voice.get(user=self.user_info.id)
        if voice.slots >= 25:
            raise MaxSlotsAmount
        price = voice.slots * price
        self.change_balance(-price)
        self.save()

        voice.slots += 1
        voice.save()

    def buy_bitrate(self, price):
        voice = Personal_voice.get(user=self.user_info.id)
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
        other = Member_data_controller(id=pair_id)
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
        roles = User_roles.select(User_roles.role_id).where(
            User_roles.user == self.user_info.id).dicts().execute()
        roles = [list(role.values())[0] for role in roles]
        return roles

    @property
    def level(self) -> tuple[int]:
        """Return tuple(level, gained_after_lvl_up, left_before_lvl_up)"""
        current_exp = self.user_info.experience
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
            Relationship.user == self.user_info.id
            or Relationship.soul_mate == self.user_info.id)
        if not relationship:
            return None

        if raw:
            return relationship[0]
        else:
            return relationship.dicts().execute()[0]

    def _change_like(self, to_member: discord.Member, type: bool):
        to_member_id = to_member.id
        Member_data_controller(to_member_id)
        like, created = Likes.get_or_create(user=self.user_info.id,
                                            to_user=to_member_id)
        if like.type == type:
            raise AlreadyLiked
        if type == 0:
            like.delete_instance()
            return
        like.type = type
        like.save()
