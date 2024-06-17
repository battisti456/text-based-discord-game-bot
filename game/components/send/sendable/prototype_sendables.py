from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from game.components.send.sendable.sendable import Sendable

if TYPE_CHECKING:
    from game.components.send.option import Option
    from smart_text import TextLike
    from game.components.send.send_address import Send_Address

@dataclass(frozen=True)
class Text(Sendable, is_prototype = True):
    text:TextLike = field()

@dataclass(frozen=True)
class Attach_Files(Sendable, is_prototype = True):
    attach_files:list[str] = field()

@dataclass(frozen=True)
class With_Options(Sendable, is_prototype = True):
    with_options:list[Option] = field()

@dataclass(frozen=True)
class Reference_Message(Sendable, is_prototype = True):
    reference_message:Send_Address = field()