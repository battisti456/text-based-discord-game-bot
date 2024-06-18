from dataclasses import dataclass

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.components.send.send_address import Send_Address
    from utils.types import PlayerId
    from game.components.send import Sendable, Option

@dataclass(frozen=True)
class Interaction_Content():
    ...
@dataclass(frozen=True)
class Command(Interaction_Content):
    text:'str'
@dataclass(frozen=True)
class Send_Text(Interaction_Content):
    text:'str'
@dataclass(frozen=True)
class Select_Options(Interaction_Content):
    options:'tuple[Option,...]'
@dataclass(frozen = True)
class Interaction():
    at_address:'Send_Address'
    with_sendable:'Sendable'
    by_player:'PlayerId'
    at_time:'float'
    content:'Interaction_Content'

