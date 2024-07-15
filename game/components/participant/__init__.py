from typing import Mapping, Optional

from typing_extensions import TypeVar

from game.components.participant.participant import Participant
from game.components.participant.player import Player
from game.components.participant.team import Team
from utils.types import Grouping, Placement

ParticipantVar = TypeVar('ParticipantVar',bound=Participant,default=Player)

type PlayerPlacement = Placement[Player]
type Players = Grouping[Player]

type PlayerDictOptional[DataType] = dict[Player,Optional[DataType]]
type PlayerDict[DataType] = dict[Player,DataType]
type PlayerMapOptional[DataType] = Mapping[Player,Optional[DataType]]
type PlayerMap[DataType] = Mapping[Player,DataType]
type TeamDict[R] = dict[Team,R]