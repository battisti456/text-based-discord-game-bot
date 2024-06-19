from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from smart_text import TextLike
    from game.components.send import Interaction

@dataclass(frozen = True)
class Response():
    to_interaction:'Interaction'
    reason:'Optional[TextLike]' = None
    reject_interaction:bool = False
    def to_text(self) -> str:
        not_text:str = ""
        if not self.reject_interaction:
            not_text = "not "
        reason:'TextLike' = ""
        if self.reason is not None:
            reason = self.reason
        return self.to_interaction.to_text()+" has " + not_text + "been rejected" + reason + "."