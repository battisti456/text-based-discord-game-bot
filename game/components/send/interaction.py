from dataclasses import dataclass

from typing import TYPE_CHECKING, override

from game import get_logger

from utils.grammar import wordify_iterable

if TYPE_CHECKING:
    from game.components.send.address import Address
    from utils.types import PlayerId
    from game.components.send import Sendable, Option
    from smart_text import TextLike

logger = get_logger(__name__)

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
class Interaction():
    at_address:'Address|None'
    with_sendable:'Sendable|None'
    by_player:'PlayerId'
    at_time:'float'
    content:'Interaction_Content'
    def __post_init__(self):
        logger.debug(f"Generated interaction:{self}")
    def to_text(self) -> 'TextLike':
        return "interaction of " + self.content.to_words()

