from enum import Enum


class EventName(str, Enum):
    MONITORING_GUILD_PROMOTED = 'monitoring_guild_promoted'
    AUCTION_ITEM_SOLD = 'auction_item_sold'
    
