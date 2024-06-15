import dataclasses
from typing import override, Any, TYPE_CHECKING

from game.components.message.content_part import Content, PlayerMessage
from game.components.message.message_part import Message_Part
from game.components.message.message_part_manager import Message_Part_Manager
from game.components.message.option import Option

from utils.common import Singleton

if TYPE_CHECKING:
    from game.components.message.message import Message

@dataclasses.dataclass(frozen=True)
class Base_Interactable[T](Message_Part,is_prototype=True):
    ...

@dataclasses.dataclass(frozen= True)
class Receive_Text(Base_Interactable[PlayerMessage],metaclass = Singleton):
    ...

@dataclasses.dataclass(frozen=True)
class Replying_To(Base_Interactable['Message'], metaclass = Singleton):
    ...

@dataclasses.dataclass(frozen=True)
class ToggleSelection(Base_Interactable[tuple[bool,Option]], Content[set[Option]]):
    ...

class Interaction(dict[type[Base_Interactable[Any]],Any]):
    def __init__(self):
        super().__init__()
    @override
    def __getitem__[T](self, key: type[Base_Interactable[T]]) -> T:
        return super().__getitem__(key)
    @override
    def __setitem__[T](self, key: type[Base_Interactable[T]], value: T) -> None:
        return super().__setitem__(key, value)