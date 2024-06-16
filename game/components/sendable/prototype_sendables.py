from dataclasses import dataclass
from typing import TYPE_CHECKING

from game.components.sendable.sendable import Sendable

if TYPE_CHECKING:
    from utils.types import ChannelId
    from smart_text import TextLike

@dataclass
class Text(Sendable):
    text:TextLike

@dataclass
class On_Channel(Sendable):
    on_channel:ChannelId