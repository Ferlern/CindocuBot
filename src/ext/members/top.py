from typing import Sequence
import disnake
from disnake.ext import commands
import peewee
from datetime import datetime, time
import asyncio

from src.database.models import Members, Likes, GameStatistics, psql_db, RelationshipTopEntry
from src.formatters import ordered_list
from src.discord_views.embeds import DefaultEmbed
from src.utils.experience import format_exp
from src.utils.time_ import display_time
from src.ext.economy.services import get_economy_settings
from src.ext.members.services import reset_members_activity, give_activity_rewards
from src.translation import get_translator
from src.discord_views.base_view import BaseView
from src.logger import get_logger
from src.bot import SEBot




logger = get_logger()
t = get_translator(route="ext.top")
TOP_SIZE = 10
REWARD_CHANNEL = 1212035478430158938
REWARDS = {
    1: "2000",
    2: "1000",
    3: "500"
}

class TopCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot

    @commands.Cog.listener()    
    async def on_ready(self):
        year = datetime.today().year
        first_days_of_month = [datetime(year, month, 1).date() for month in range(1, 13)]
        target_time = time(hour=0, minute=0).strftime('%H:%M')
        logger.info("month listener started successfully")
        while True:
            current_time = datetime.utcnow()
            if (current_time.date() in first_days_of_month) and (current_time.strftime('%H:%M') == target_time):
                channel = self.bot.get_channel(REWARD_CHANNEL)
                guild_id = channel.guild.id

                try:
                    logger.info("sending message with rewards on guild: %s", channel.guild)
                    await channel.send(embed=create_rewards_embed(guild_id))
                    
                    give_activity_rewards(guild_id, REWARDS)
                    reset_members_activity(guild_id)
                except Exception as e:
                    logger.error("tried to sum up the month but an error occured: %s", repr(e))

            await asyncio.sleep(60)  
        
    @commands.slash_command()
    async def top(
        self,
        inter: disnake.GuildCommandInteraction,
    ) -> None:
        """
        Посмотреть топы участников этого сервера
        """
        guild = inter.guild
        view = TopView(guild_id=guild.id)
        await view.start_from(inter)


class TopView(BaseView):
    def __init__(self, guild_id: int) -> None:
        super().__init__()
        self.guild_id = guild_id
        self.top_map = {
            t('top_select_voice'): create_voice_top_embed,
            t('top_select_activity'): create_chat_activity_top_embed,
            t('top_select_balance'): create_balance_top_embed,
            t('top_select_reputation'): create_reputation_top_embed,
            t('top_select_experience'): create_experience_top_embed,
            t('top_select_relationship'): create_relationships_top_embed,
            t('top_select_games'): create_games_top_embed,
        }
        self.add_item(TopSelect(self.top_map))

    async def _response(self, inter: disnake.ApplicationCommandInteraction) -> None:
        await inter.response.send_message(
            embed=list(self.top_map.values())[0](self.guild_id),
            view=self,
        )


class TopSelect(disnake.ui.Select):
    view: TopView

    def __init__(self, top_map) -> None:
        options = [
            disnake.SelectOption(
                label=name,
            ) for name in top_map
        ]
        super().__init__(options=options)

    async def callback(
        self,
        interaction: disnake.MessageInteraction,
        /
    ) -> None:
        name = self.values[0]
        await interaction.response.edit_message(
            embed=self.view.top_map[name](self.view.guild_id),
            view=self.view,
        )


def _build_members_top_query(
    guild_id: int,
    ordering: peewee.Ordering,
):
    return (
        Members.
        select(Members).
        where((Members.guild_id == guild_id) & (Members.on_guild == True)).  # noqa
        order_by(ordering).  # type: ignore
        limit(TOP_SIZE)
    )


def _build_voice_top_query(guild_id: int):
    return _build_members_top_query(
        guild_id=guild_id,
        ordering=-Members.voice_activity,  # type: ignore
    )


def _build_balance_top_query(guild_id: int):
    return _build_members_top_query(
        guild_id=guild_id,
        ordering=-Members.balance,  # type: ignore
    )


def _build_experience_top_query(guild_id: int):
    return _build_members_top_query(
        guild_id=guild_id,
        ordering=-Members.experience,  # type: ignore
    )

def _build_chat_activity_top_query(guild_id: int):
    return _build_members_top_query(
        guild_id=guild_id,
        ordering=-Members.monthly_chat_activity,
    )

def _build_reputation_top_query(guild_id: int):
    reputation_sum = peewee.fn.COALESCE(peewee.fn.sum(Likes.type), 0)
    return (
        Members.select(
            Members.user_id,
            reputation_sum.alias('reputation'),
        ).
        join(
            Likes,
            join_type=peewee.JOIN.LEFT_OUTER,
            on=Members.user_id == Likes.to_user_id
        ).
        where((Members.guild_id == guild_id) & (Members.on_guild == True)).  # type: ignore # noqa
        order_by(peewee.SQL('reputation DESC')).
        group_by(Members.user_id).
        limit(TOP_SIZE)
    )


def _build_relations_top_query(guild_id: int) -> list[RelationshipTopEntry]:
    querry = """
    WITH rp AS (
        SELECT
            creation_time,
            r.id rel_id,
            m.user_id,
            row_number() OVER(PARTITION BY r.id)
        FROM Relationships r
        INNER JOIN RelationshipParticipant rp ON r.id = rp.relationship_id
        INNER JOIN Members m ON rp.user_id = m.user_id
        WHERE m.on_guild = TRUE AND m.guild_id = %s
        ORDER BY creation_time
    )
    SELECT rp1.creation_time, rp1.user_id first_user, rp2.user_id second_user FROM rp rp1
    INNER JOIN rp rp2 ON
        rp1.rel_id = rp2.rel_id AND
        rp1.user_id != rp2.user_id AND
        rp1.row_number = 1
    LIMIT 10;
    """
    entrys = psql_db.execute_sql(querry, (guild_id,)).fetchall()
    return [RelationshipTopEntry(*entry) for entry in entrys]


def _build_games_top_query(guild_id: int) -> Sequence[GameStatistics]:
    return GameStatistics.select().where(
        GameStatistics.guild == guild_id
    ).order_by(-GameStatistics.wins).limit(TOP_SIZE)


def create_voice_top_embed(guild_id: int) -> disnake.Embed:
    query = _build_voice_top_query(guild_id)
    desc = ordered_list(
        query,
        lambda item: f'<@{item.user_id}> — {display_time(item.voice_activity)}'  # noqa
    )
    return DefaultEmbed(
        title=t('top_voice'),
        description=desc,
    )


def create_experience_top_embed(guild_id: int) -> disnake.Embed:
    query = _build_experience_top_query(guild_id)
    desc = ordered_list(
        query,
        lambda item: f'<@{item.user_id}> — {format_exp(item.experience)}'  # noqa
    )
    return DefaultEmbed(
        title=t('top_experience'),
        description=desc,
    )

def create_chat_activity_top_embed(guild_id: int) -> disnake.Embed:
    query = _build_chat_activity_top_query(guild_id)
    settings = get_economy_settings(guild_id)
    top = ordered_list(
        query,
        lambda item: f'<@{item.user_id}> — **{item.monthly_chat_activity}** опыта'
    ).split('\n')
    desc = '\n'.join([item + f'  **|**  {REWARDS[index + 1]} {settings.coin}' if index < len(REWARDS) else item for index, item in enumerate(top)])
    return DefaultEmbed(
        title=t('top_activity'),
        description=desc,
    )   

def create_rewards_embed(guild_id: int) -> disnake.Embed:
    query = _build_chat_activity_top_query(guild_id)
    settings = get_economy_settings(guild_id)
    top = ordered_list(
        query,
        lambda item: f'<@{item.user_id}> — ' 
    ).split('\n')[:len(REWARDS)]
    desc = '\n'.join([item + f'{REWARDS[index + 1]} {settings.coin}' for index, item in enumerate(top)])

    embed = disnake.Embed(
        title = t('monthly_rewards_title'),
        description = desc + '\n\n' + t('activity_thanks'),
    )   
    embed.set_image(url='https://imgur.com/iXIpPd8.gif')
    return embed

def create_balance_top_embed(guild_id: int) -> disnake.Embed:
    query = _build_balance_top_query(guild_id)
    settings = get_economy_settings(guild_id)
    desc = ordered_list(
        query,
        lambda item: f'<@{item.user_id}> — {item.balance} {settings.coin}'
    )
    return DefaultEmbed(
        title=t('top_balance'),
        description=desc,
    )


def create_reputation_top_embed(guild_id: int) -> disnake.Embed:
    query = _build_reputation_top_query(guild_id)
    desc = ordered_list(
        query,
        lambda item: f'<@{item.user_id}> — {item.reputation} :revolving_hearts:'  # noqa
    )
    return DefaultEmbed(
        title=t('top_reputation'),
        description=desc,
    )


def create_relationships_top_embed(guild_id: int) -> disnake.Embed:
    items = _build_relations_top_query(guild_id)

    def formatter(item: RelationshipTopEntry) -> str:
        first_user = f'<@{item.first_user_id}>'
        second_user = f'<@{item.second_user_id}>'
        timestamp = disnake.utils.format_dt(item.creation_time, 'f')
        return t(
            'relationship_repr',
            first_user=first_user,
            second_user=second_user,
            timestamp=timestamp,
        )

    desc = ordered_list(items, formatter)
    return DefaultEmbed(
        title=t('top_relationship'),
        description=desc,
    )


def create_games_top_embed(guild_id: int) -> disnake.Embed:
    query = _build_games_top_query(guild_id)
    economy_settings = get_economy_settings(guild_id)
    coin = economy_settings.coin

    def formatter(item: GameStatistics) -> str:
        return t(
            'games_repr',
            user_id=item.user_id,  # type: ignore
            wins=t('wins', count=item.wins),
            money=item.money_won,
            coin=coin,
        )
    desc = ordered_list(
        query,
        formatter
    )
    return DefaultEmbed(
        title=t('top_games'),
        description=desc,
    )


def setup(bot) -> None:
    bot.add_cog(TopCog(bot))
