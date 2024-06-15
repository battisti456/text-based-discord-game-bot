import dataclasses

from message_part import Message_Part

from utils.types import ChannelId, PlayerId

@dataclasses.dataclass(frozen=True)
class Utility_Part(Message_Part):
    ...
@dataclasses.dataclass(frozen=True)
class Player_Utility(Utility_Part):
    players:set[PlayerId]
@dataclasses.dataclass(frozen=True)
class Limit_Viewers(Player_Utility):
    ...
@dataclasses.dataclass(frozen=True)
class Limit_Interactors(Player_Utility):
    ...
@dataclasses.dataclass(frozen=True)
class Channel_Utility(Utility_Part):
    channel_id:ChannelId
@dataclasses.dataclass(frozen=True)
class On_Channel(Channel_Utility):
    ...