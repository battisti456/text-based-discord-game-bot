from dataclasses import dataclass
from typing import override, Optional, Mapping

from typing_extensions import TypeVar

from utils.types import GS, Grouping, Placement


@dataclass(frozen=True)
class Participant(GS):
    ...

class Player(Participant):
    ...

@dataclass(frozen=True)
class Team(Participant):
    string:str
    @override
    def __str__(self) -> str:
        return self.string
    
ParticipantVar = TypeVar('ParticipantVar',bound=Participant,default=Player)

type PlayerPlacement = Placement[Player]
type Players = Grouping[Player]

type PlayerDictOptional[DataType] = dict[Player,Optional[DataType]]
type PlayerDict[DataType] = dict[Player,DataType]
type PlayerMapOptional[DataType] = Mapping[Player,Optional[DataType]]
type PlayerMap[DataType] = Mapping[Player,DataType]
type TeamDict[R] = dict[Team,R]