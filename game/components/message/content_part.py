import dataclasses
from typing import TYPE_CHECKING, override

from game.components.message.message_part import Message_Part
from game.components.message.message_part_manager import Message_Part_Manager
from game.types import FilePath, ImagePath, ImagePathWithCaption, PlayerMessage
from utils.grammar import temp_file_path

if TYPE_CHECKING:
    import PIL.Image

@dataclasses.dataclass(frozen=True)
class Content[T](Message_Part,is_prototype=True):
    content:T
    @override
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.content})"
@dataclasses.dataclass(frozen=True)
class Message_Text(Content[str]):
    @classmethod
    @override
    def merge(cls,parts:set['Message_Part']) -> 'Message_Text':
        alike = cls.alike_parts(parts)
        return Message_Text('\n'.join(part.content for part in alike))
@dataclasses.dataclass(frozen=True)
class Attach_File(Content[FilePath]):
    ...
@dataclasses.dataclass(frozen=True)
class Embed_Image(Content[ImagePath]):
    @classmethod
    def from_image(cls,image:'PIL.Image.Image') -> 'Embed_Image':
        path = temp_file_path('.png')
        image.save(path)
        return Embed_Image(path)
    @override
    def _comply_to(self, types: set[type[Message_Part]]) -> Message_Part_Manager:
        if Attach_File in types:
            return Message_Part_Manager((Attach_File(self.content),))
        return super()._comply_to(types)
@dataclasses.dataclass(frozen=True)
class Embed_Image_With_Caption(Content[ImagePathWithCaption]):
    @override
    def _comply_to(self, types: set[type[Message_Part]]) -> Message_Part_Manager:
        to_return = Message_Part_Manager()
        if Embed_Image in types:
            to_return.add(Embed_Image(self.content[0]))
        elif Attach_File in types:
            to_return.add(Attach_File(self.content[0]))
        if Message_Text in types:
            to_return.add(Message_Text(self.content[1]))
        if to_return:
            return to_return
        return super()._comply_to(types)
@dataclasses.dataclass(frozen=True)
class Reply_To_Player_Message(Content[PlayerMessage]):
    ...