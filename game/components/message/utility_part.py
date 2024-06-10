from message_part import Message_Part
from game import PlayerId
import dataclasses
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