from typing import TypedDict

    
class Profile_emoji(TypedDict):
    reputation: str
    balance: str
    level: str
    voice: str
    soul_mate: str
    other: str
    
    
class Top_emoji(TypedDict):
    reputation: str
    balance: str
    level: str
    voice: str
    soul_mate: str
    
    
class Economy_emoji(TypedDict):
    daily_recieved: str
    daily_cooldown: str
    roles_shop: str
    voice_shop: str
    
    
class Relationship_emoji(TypedDict):
    sent: str
    accepted: str
    refused: str
    divorce: str
    
    
class Reputation_emoji(TypedDict):
    increased: str
    decreased: str
    reset: str


class Suggestion_emoji(TypedDict):
    list: str
    send: str


class Other_emoji(TypedDict):
    heart: str
    all_mod_log: str


class Additional_emoji(TypedDict):
    profile: Profile_emoji
    top: Top_emoji
    economy: Economy_emoji
    relationship: Relationship_emoji
    reputation: Reputation_emoji
    suggestion: Suggestion_emoji
    other: Other_emoji
    