from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from game.components.message.message import Message


class Message_Part():
    def __init__(
            self):
        ...
    def bind(self,message:'Message'):
        message.parts.add(self)
    @override
    def __hash__(self) -> int:
        return hash(self.__class__.__name__)
        