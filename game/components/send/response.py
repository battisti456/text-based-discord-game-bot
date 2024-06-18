from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from smart_text import TextLike

@dataclass(frozen = True)
class Response():
    text:'Optional[TextLike]' = None
    reject_interaction:bool = False
    def __or__(self, value: 'Response') -> 'Response':
        text:'Optional[TextLike]' = self.text
        if value.text is not None:
            if text is None:
                text = value.text
            else:
                text += '\n' + value.text#type:ignore
        return Response(text, self.reject_interaction or value.reject_interaction)