from dataclasses import dataclass
from typing import (
    Iterator,
    Literal,
    Mapping,
    NewType,
    Optional,
    Protocol,
    runtime_checkable,
    override,
    Hashable
)

from typing_extensions import TypeVar


@dataclass(frozen=True)
class GS():
    "Base class for grouping safe objects that aren't explicit."
    ...

PlayerId = NewType('PlayerId',GS)#type: ignore
MessageId = NewType('MessageId',GS)#type: ignore
ChannelId = NewType('ChannelId',GS)#type: ignore
InteractionId = NewType('InteractionId',GS)#type: ignore

type PlayersIds = Grouping[PlayerId]

type Placement[T] = tuple[tuple[T,...],...]

type PlayerPlacement = Placement[PlayerId]

type PlayerDictOptional[DataType] = dict[PlayerId,Optional[DataType]]
type PlayerDict[DataType] = dict[PlayerId,DataType]
type PlayerMapOptional[DataType] = Mapping[PlayerId,Optional[DataType]]
type PlayerMap[DataType] = Mapping[PlayerId,DataType]

type KickReason = Literal['timeout','eliminated','unspecified']

type Operators = Literal['command','run_game']

@dataclass(frozen=True)
class Team(GS):
    string:str
    @override
    def __str__(self) -> str:
        return self.string


type TeamDict[R] = dict[Team,R]


Participant = TypeVar('Participant',bound=Team|PlayerId,default=PlayerId)
IDType = TypeVar('IDType',bound=Hashable,default = str)

GroupingSafe = int|float|GS#strings cannot be grouping safe, unfortunately
GroupingSafeVar = TypeVar('GroupingSafeVar',bound = GroupingSafe)
@runtime_checkable
class Grouping(Protocol[GroupingSafeVar]):
    """
    a type that incudes all iterable objects that are parametized (so excludes strings)
    """
    def __iter__(self) -> Iterator[GroupingSafeVar]:
        ...
    def __contains__(self,key:GroupingSafeVar, /) -> bool:
        ...
    def __len__(self) -> int:
        ...

type Number = int|float