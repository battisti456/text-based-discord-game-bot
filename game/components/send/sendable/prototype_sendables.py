from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from game.components.send.sendable.sendable import Sendable

if TYPE_CHECKING:
    from game.components.send.option import Option
    from smart_text import TextLike
    from game.components.send.send_address import Send_Address

@dataclass(frozen=True)
class Text(Sendable, is_prototype = True):
    text:'TextLike' = field(kw_only=True)

@dataclass(frozen=True)
class Attach_Files(Sendable, is_prototype = True):
    attach_files:'tuple[str,...]' = field(kw_only=True)

@dataclass(frozen=True)
class With_Options(Sendable, is_prototype = True):
    with_options:'tuple[Option,...]' = field(kw_only=True)
    min_selectable:'Optional[int]' = field(default=None,kw_only=True)
    max_selectable:'Optional[int]' = field(default=None,kw_only=True)
@dataclass(frozen = True)
class With_Text_Field(Sendable, is_prototype = True):
    hint_text:Optional['TextLike'] = field(default=None,kw_only=True)
@dataclass(frozen=True)
class Reference_Message(Sendable, is_prototype = True):
    reference_message:'Send_Address' = field(kw_only=True)