import dataclasses

from game.components.message.message_part import Message_Part


@dataclasses.dataclass(frozen=True)
class Content[T](Message_Part):
    content:T
@dataclasses.dataclass(frozen=True)
class Message_Text(Content[str]):
    ...
@dataclasses.dataclass(frozen=True)
class Embedded_File(Content[str]):
    ...
