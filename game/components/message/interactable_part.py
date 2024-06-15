import dataclasses
from typing import Awaitable, override

from game.components.message.content_part import Content, PlayerMessage
from game.components.message.message_part import Message_Part
from game.components.message.message_part_manager import Message_Part_Manager
from game.components.message.option import Option
from utils.types import SimpleFunc


@dataclasses.dataclass(frozen=True)
class Base_Interactable[T](Message_Part):
    bound_functions:list[SimpleFunc[T]] = []
    async def interact(self,interaction:T):
        for function in self.bound_functions:
            b = function(interaction)
            if isinstance(b,Awaitable):
                await b
    def on_interact(self,callback:SimpleFunc[T]):
        self.bound_functions.append(callback)
@dataclasses.dataclass(frozen= True)
class Receive_All_Messages(Base_Interactable[PlayerMessage]):
    ...
@dataclasses.dataclass(frozen=True)
class Receive_Command(Receive_All_Messages,Content[str]):
    @override
    async def interact(self, interaction: PlayerMessage):
        if interaction[1] is None:
            return
        if interaction[1].startswith(self.content):
            return await super().interact(interaction)
    @override
    def _comply_to(self, types: set[type[Message_Part]]) -> Message_Part_Manager:
        if Receive_All_Messages in types:
            return Message_Part_Manager((Receive_All_Messages(bound_functions=[self.interact]),))
        return super()._comply_to(types)
@dataclasses.dataclass(frozen=True)
class Reply_Able(Base_Interactable[PlayerMessage]):
    ...
@dataclasses.dataclass(frozen=True)
class Single_Selectable(Base_Interactable[Option], Content[set[Option]]):
    ...