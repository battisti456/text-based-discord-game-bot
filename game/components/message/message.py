from typing import Any, Callable, Iterable, Iterator, Literal, override, Awaitable

from game.components.message.content_part import Message_Text, Content
from game.components.message.message_part import Message_Part
from game.components.message.message_part_manager import Message_Part_Manager
from game.components.message.utility_part import On_Channel
from game.components.message.interactable_part import Interaction
from game.components.message.option import Option
from utils.types import ChannelId, SimpleFunc

type MessageSearchStrictness = Literal["original","aliases","children",'sub_aliases','sub_children']
type OnReadFunc = Callable[['Child_Message'],None]


class Message(Message_Part_Manager):
    def __init__(
            self,
            content:str|Message_Part|Iterable[Message_Part] = [],
            funcs:Iterable[Callable[[Interaction],None]] = []):
        if isinstance(content,str):
            content = Message_Text(content)
        if isinstance(content,Message_Part):
            self.add(content)
        else:
            self.add_all(content)
        self.children:set[Message] = set()
        self._interact_funcs:list[SimpleFunc[Interaction]] = list(funcs)
    def is_interactable(self,interaction:Interaction) -> bool:
        return set(self.keys()).issubset(set(interaction.keys()))
    @override
    def __str__(self) -> str:
        return f"{self.__class__.__name__}{tuple(self.values())}"
    @override
    def __repr__(self) -> str:
        return str(self)
    def on_interact(self,func:SimpleFunc[Interaction]):
        self._interact_funcs.append(func)
    async def interact(self,interaction:Interaction):
        for func in self._interact_funcs:
            ret = func(interaction)
            if isinstance(ret,Awaitable):
                await ret
    def options(self) -> Iterable[Option]:
        for part in self.values():
            if isinstance(part,Content):
                if isinstance(part.content,Iterable):
                    for sub_content in part.content:
                        if not isinstance(sub_content,Option):
                            break
                        yield sub_content


class Child_Message(Message):
    def __init__(self,parent_message:'Message'):
        self.parent_message = parent_message
        self.parent_message.children.add(self)
        super().__init__()
    @override
    def __getitem__(self, key: type[Message_Part]) -> Message_Part:
        if key in self:
            return super().__getitem__(key)
        return self.parent_message[key]
    @override
    def keys(self) -> Iterator[type[Message_Part]]:
        for key in super().keys():
            yield key
        for key in self.parent_message.keys():
            if key not in self:
                yield key
    @override
    def values(self) -> Iterator[Message_Part]:
        for key in self.keys():
            yield self[key]
    @override
    def items(self) -> Iterator[tuple[type[Message_Part], Message_Part]]:
        for key in self.keys():
            yield (key,self[key])

class Updating_Message(Child_Message):
    def __init__(self,parent_message:'Message'):
        super().__init__(parent_message)
        self.on_read_funcs:list[OnReadFunc] = []
    def on_read(self,func:OnReadFunc):
        self.on_read_funcs.append(func)
    def do_on_read(self):
        for func in self.on_read_funcs:
            func(self)
    @override
    def __getattribute__(self, name: str) -> Any:
        self.do_on_read()
        return super().__getattribute__(name)

class Reroute_Message(Child_Message):
    def __init__(self,parent_message:Message,channel:ChannelId|On_Channel):
        super().__init__(parent_message)
        if not isinstance(channel,On_Channel):
            channel = On_Channel(channel)
        self.add(channel)

class Receive_Command_Message(Message):
    def __init__(self, command_str:str):
        super().__init__((
            Message_Text(f"Listening for commands starting with '{command_str}'."),
            Receive_Command(command_str)
        ))
