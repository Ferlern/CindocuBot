from typing import TypedDict

    
class ProfileEmoji(TypedDict):
    reputation: str
    balance: str
    level: str
    voice: str
    soul_mate: str
    other: str
    
    
class TopEmoji(TypedDict):
    reputation: str
    balance: str
    level: str
    voice: str
    soul_mate: str
    
    
class EconomyEmoji(TypedDict):
    daily_recieved: str
    daily_cooldown: str
    roles_shop: str
    voice_shop: str
    
    
class RelationshipEmoji(TypedDict):
    sent: str
    accepted: str
    refused: str
    divorce: str
    
    
class ReputationEmoji(TypedDict):
    increased: str
    decreased: str
    reset: str


class SuggestionEmoji(TypedDict):
    list: str
    send: str


class OtherEmoji(TypedDict):
    heart: str
    all_mod_log: str


class AdditionalEmoji(TypedDict):
    profile: ProfileEmoji
    top: TopEmoji
    economy: EconomyEmoji
    relationship: RelationshipEmoji
    reputation: ReputationEmoji
    suggestion: SuggestionEmoji
    other: OtherEmoji
    