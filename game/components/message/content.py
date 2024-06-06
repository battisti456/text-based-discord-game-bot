from typing import Optional

from game.components.message.message_part import Message_Part

class Content[T](Message_Part):
    def __init__(
            self,
            content:T):
        super().__init__()
        self.content = content

class Message_Text(Content[str]):
    def __init__(self, content: Optional[str]):
        if content is None:
            content = "--empty--"
        super().__init__(content)

class Embedded_File(Content[str]):
    ...
