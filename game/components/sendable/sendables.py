from dataclasses import dataclass

from game.components.sendable.prototype_sendables import On_Channel, Text

@dataclass
class Old_Message(
    Text,
    On_Channel
):
    ...