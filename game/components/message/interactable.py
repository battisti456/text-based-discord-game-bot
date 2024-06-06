from typing import Callable

from game.components.message.message_part import Message_Part
from game.components.message.content import Content
from game.components.message.option import Option

class Base_Interactable[T](Message_Part):
    def __init__(self):
        self.bound_functions:list[Callable[[T],None]]
    def interact(self,interaction:T):
        ...
    def on_interact(self,callback:Callable[[T],None]):
        self.bound_functions.append(callback)
class Reply_Able(Base_Interactable[None]):
    ...
class Single_Selectable(Base_Interactable[Option], Content[set[Option]]):
    ...

