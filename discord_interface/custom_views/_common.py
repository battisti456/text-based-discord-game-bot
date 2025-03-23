from typing import TYPE_CHECKING
from discord_interface.common import f

if TYPE_CHECKING:
    from game.components.send.sendable.prototype_sendables import With_Text_Field


def hint_text(sendable: "With_Text_Field") -> str:
    return (
        "Input your response here!"
        if sendable.hint_text is None
        else f(sendable.hint_text)
    )
