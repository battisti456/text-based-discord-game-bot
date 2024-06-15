from typing import override, Iterable, TYPE_CHECKING, Never

if TYPE_CHECKING:
    from game.components.message.message_part import Message_Part

class Message_Part_Manager(dict[type[Message_Part],Message_Part]):
    def __init__(self,values:Iterable[Message_Part] = tuple()):
        super().__init__({
            value.__class__:value for value in values
        })
    def add(self,message_part:Message_Part):
        dict.__setitem__(self,message_part.__class__,message_part)
    def has(self,message_part:Message_Part|type[Message_Part]) -> bool:
        return message_part.part_type(message_part) in self.keys()
    def remove(self,message_part:Message_Part|type[Message_Part]):
        del self[message_part.part_type(message_part)]
    def add_all(self,message_parts:Iterable[Message_Part]):
        for message_part in message_parts:
            self.add(message_part)
    @override
    def __getitem__[T](self, key: type[T]) -> T:
        return super().__getitem__(key)#type:ignore
    @override
    def __setitem__(self, *_: Never):
        raise NotImplementedError("Message part managers do not support direct assignment of keys. Use Message_Part_Manager.add instead")
    def conflicts(self,other:'Message_Part_Manager') -> bool:
        return any(
            tpe in other and other[tpe] != val
            for tpe,val in self.items()
            )
    @override
    def __or__(self, value: 'Message_Part_Manager') -> 'Message_Part_Manager':
        return Message_Part_Manager(dict.__or__(self,value))
    @override
    def __ror__(self, value: 'Message_Part_Manager') -> 'Message_Part_Manager':
        return Message_Part_Manager(dict.__ror__(self,value))

