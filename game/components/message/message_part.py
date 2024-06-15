import dataclasses
from typing import TYPE_CHECKING, override

from game import get_logger
from utils.common import get_first

if TYPE_CHECKING:
    from game.components.message.message import Message
from game.components.message.message_part_manager import Message_Part_Manager

logger = get_logger(__name__)

type MessagePartTypeSet = set[type['Message_Part']]


@dataclasses.dataclass(frozen=True)
class Message_Part():
    def bind(self,message:'Message'):
        message.add(self)
    def comply_to(self,types:MessagePartTypeSet) -> Message_Part_Manager:
        if self.__class__ in types:
            return Message_Part_Manager((self,))
        else:
            return self._comply_to(types)
    def _comply_to(self,types:MessagePartTypeSet) -> Message_Part_Manager:
        logger.warning(f"complying by removing {self}")
        return Message_Part_Manager()
    @classmethod
    def alike_parts[T](cls:type[T],parts:set['Message_Part']) -> set[T]:
        return set(part for part in parts if isinstance(part,cls))
    @classmethod
    def merge[T](cls:type[T],parts:set['Message_Part']) -> T:
        alike:set[T] = cls.alike_parts(parts)#type:ignore
        if not alike:
            raise IndexError(f"{cls} does not exist in {parts}")
        to_return = get_first(alike)
        if len(alike) != 1:
            logger.warning(f"reducing {alike} to {to_return}")
        return to_return
    @override
    def __str__(self) -> str:
        return f"{self.__class__.__name__}()"
    @override
    def __repr__(self) -> str:
        return str(self)
    @classmethod
    def part_type(cls,message_part:'Message_Part'|type['Message_Part']) -> type['Message_Part']:
        return message_part.__class__ if isinstance(message_part,Message_Part) else message_part

