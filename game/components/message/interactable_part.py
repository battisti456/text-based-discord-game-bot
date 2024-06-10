import dataclasses
from typing import Awaitable, Callable

from game.components.message.content_part import Content
from game.components.message.message_part import Message_Part
from game.components.message.option import Option

type OnInteract[T] = Callable[[T],None]|Callable[[T],Awaitable[T]]

@dataclasses.dataclass(frozen=True)
class Base_Interactable[T](Message_Part):
    bound_functions:list[OnInteract[T]] = []
    async def interact(self,interaction:T):
        for function in self.bound_functions:
            b = function(interaction)
            if isinstance(b,Awaitable):
                await b
    def on_interact(self,callback:Callable[[T],None]):
        self.bound_functions.append(callback)
@dataclasses.dataclass(frozen=True)
class Reply_Able(Base_Interactable[None]):
    ...
@dataclasses.dataclass(frozen=True)
class Single_Selectable(Base_Interactable[Option], Content[set[Option]]):
    ...