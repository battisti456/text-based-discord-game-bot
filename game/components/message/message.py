from typing import Callable, Iterable, Iterator, Literal, override

from game.components.message.content_part import Message_Text
from game.components.message.message_part import Message_Part, Message_Part_Manager

type MessageSearchStrictness = Literal["original","aliases","children",'sub_aliases','sub_children']
type OnReadFunc = Callable[['Child_Message'],None]


class Message(Message_Part_Manager):
    """
    an object storing all the values which can be included in a message from the bot to the players, meant to be sent with a sender; all values are optional

    content: the text content of the message

    attach_paths: a list of sting paths directing to files to be attached to the message

    channel_id: the channel on which to send the message, if None will be assigned by sender to some default when sent

    message_id: the id of the message to edit, if None will be set by sender once sent

    players_who_can_see: the list of players who are permitted to see the message, if None all players can see

    bullet_points: a list of BulletPoint objects to display in the message
    """
    def __init__(
            self,
            content:str|Message_Part|Iterable[Message_Part] = []):
        if isinstance(content,str):
            content = Message_Text(content)
        if isinstance(content,Message_Part):
            self.add(content)
        else:
            self.add_all(content)
        self.children:set[Message] = set()


class Child_Message(Message):
    def __init__(self,parent_message:'Message'):
        self.parent_message = parent_message
        self.parent_message.children.add(self)
        self.on_read_funcs:list[OnReadFunc] = []
        super().__init__()
    def on_read(self,func:OnReadFunc):
        self.on_read_funcs.append(func)
    def do_on_read(self):
        for func in self.on_read_funcs:
            func(self)
    @override
    def __getitem__(self, key: type[Message_Part]) -> Message_Part:
        self.update()
        if key in self:
            return super().__getitem__(key)
        return self.parent_message[key]
    @override
    def keys(self) -> Iterator[type[Message_Part]]:
        self.update()
        for key in super().keys():
            yield key
        for key in self.parent_message.keys():
            if key not in self:
                yield key
    @override
    def values(self) -> Iterator[Message_Part]:
        self.update()
        for key in self.keys():
            yield self[key]
    @override
    def items(self) -> Iterator[tuple[type[Message_Part], Message_Part]]:
        self.update()
        for key in self.keys():
            yield (key,self[key])