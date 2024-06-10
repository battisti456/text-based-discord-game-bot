import dataclasses
from typing import TYPE_CHECKING, Iterable, override

from game import get_logger
from utils.common import get_first

if TYPE_CHECKING:
    from game.components.message.message import Message

logger = get_logger(__name__)

type MessagePartTypeSet = set[type['Message_Part']]

@dataclasses.dataclass(frozen=True)
class Message_Part():
    def bind(self,message:'Message'):
        message.add(self)
    def comply_to(self,types:MessagePartTypeSet) -> set['Message_Part']:
        ...
    @classmethod
    def alike_parts(cls,parts:set['Message_Part']) -> set['Message_Part']:
        return set(part for part in parts if isinstance(part,cls))
    @classmethod
    def merge(cls,parts:set['Message_Part']) -> 'Message_Part':
        alike = cls.alike_parts(parts)
        to_return = get_first(alike)
        if len(alike) != 1:
            logger.warning(f"reducing {alike} to {to_return}")
        return to_return

def part_type(message_part:Message_Part|type[Message_Part]) -> type[Message_Part]:
    return message_part.__class__ if isinstance(message_part,Message_Part) else message_part
    
class Message_Part_Manager(dict[type[Message_Part],Message_Part]):
    def add(self,message_part:Message_Part):
        dict.__setitem__(self,message_part.__class__,message_part)
    def has(self,message_part:Message_Part|type[Message_Part]) -> bool:
        return part_type(message_part) in self.keys()
    def remove(self,message_part:Message_Part|type[Message_Part]):
        del self[part_type(message_part)]
    def add_all(self,message_parts:Iterable[Message_Part]):
        for message_part in message_parts:
            self.add(message_part)
    @override
    def __setitem__(self, key: type[Message_Part], value: Message_Part) -> None:
        raise NotImplementedError("Message part managers do not support direct assignment of keys. Use Message_Part_Manager.add instead")