from dataclasses import dataclass
from typing import TYPE_CHECKING, override, Generic, Callable, Any

from typing_extensions import TypeVar

from utils.logging import get_logger
from utils.grammar import wordify_iterable

if TYPE_CHECKING:
    from game.components.participant import Player
    from game.components.send import Option, Sendable
    from game.components.send.address import Address
    from smart_text import TextLike

logger = get_logger(__name__)

InteractionContentVar = TypeVar('InteractionContentVar', bound='Command|Send_Text|Select_Options')
InteractionFilter = Callable[['Interaction[InteractionContentVar]'],bool]

def no_filter(_) -> bool:
    return True

@dataclass(frozen=True)
class Interaction_Content():
    def to_words(self) -> str:
        raise NotImplementedError()
@dataclass(frozen=True)
class Command(Interaction_Content):
    text:'str'
@dataclass(frozen=True)
class Send_Text(Interaction_Content):
    text:'str'
    @override
    def to_words(self) -> str:
        return f"sent {self.text}"
@dataclass(frozen=True)
class Select_Options(Interaction_Content):
    options:'tuple[Option,...]'
    indices:tuple[int,...]
    @override
    def to_words(self) -> 'TextLike':
        return f"selected {wordify_iterable(option.text for option in self.options)}"

@dataclass(frozen = True)
class Interaction(Generic[InteractionContentVar]):
    at_address:'Address|None'
    with_sendable:'Sendable|None'
    by_player:'Player'
    at_time:'float'
    content:'InteractionContentVar'
    def __post_init__(self):
        logger.debug(f"Generated interaction:{self}")
    def to_text(self) -> 'TextLike':
        return "interaction of " + self.content.to_words()

def address_filter(address:Address) -> InteractionFilter[Any]:
    def _(interaction:Interaction):
        return interaction.at_address == address
    return _

def all_filter(*args:InteractionFilter[InteractionContentVar]) -> InteractionFilter[InteractionContentVar]:
    def _(interaction:Interaction[InteractionContentVar]) -> bool:
        return all(arg(interaction) for arg in args)
    return _

def selection_limit_filter(*,min:int=1,max:int=1) -> InteractionFilter[Select_Options]:
    def _(interaction:Interaction[Select_Options]) -> bool:
        num = len(interaction.content.options)
        return num <= max and num >= min
    return _


