from dataclasses import dataclass
from typing import (
    Iterator,
    Literal,
    Protocol,
    runtime_checkable,
    Callable,
    Awaitable
)

from typing_extensions import TypeVar

@dataclass(frozen=True)
class GS():
    "Base class for grouping safe objects that aren't explicit."
    ...

type Placement[T] = tuple[tuple[T,...],...]

type KickReason = Literal['timeout','eliminated','unspecified']

type Operators = Literal['command','run_game']

type Callback[InData,OutData] = Callable[[InData],OutData]|Callable[[InData],Awaitable[OutData]]

type SimpleCallback[Data] = Callback[Data,None]

type Tuple9[T] = tuple[T,T,T,T,T,T,T,T,T]

GroupingSafe = int|float|GS#strings cannot be grouping safe, unfortunately
GroupingSafeVar = TypeVar('GroupingSafeVar',bound = GroupingSafe)
@runtime_checkable
class Grouping(Protocol[GroupingSafeVar]):
    """
    a type that incudes all iterable objects that are parametrized (so excludes strings)
    """
    def __iter__(self) -> Iterator[GroupingSafeVar]:
        ...
    def __contains__(self,key:GroupingSafeVar, /) -> bool:
        ...
    def __len__(self) -> int:
        ...


type Number = int|float