from game.components.message.content_part import (
    Attach_File,
    Content,
    Message_Text,
    Reply_To_Player_Message,
)
from game.components.message.interactable_part import (
    Receive_All_Messages,
    Receive_Command,
    Reply_Able,
    Single_Selectable,
)
from game.components.message.message import (
    Message,
    Receive_Command_Message,
    Reroute_Message,
)
from game.components.message.message_part import (
    Message_Part,
)
from game.components.message.message_part_manager import Message_Part_Manager
from game.components.message.option import Option, make_options
from game.components.message.utility_part import (
    Limit_Interactors,
    Limit_Viewers,
    On_Channel,
)
from typing import Iterable

PART_ORDER:tuple[type['Message_Part'],...] = (
    Attach_File,
    Content,
    Message_Text,
    Reply_To_Player_Message,
    Receive_All_Messages,
    Receive_Command,
    Reply_Able,
    Single_Selectable,
    Limit_Interactors,
    Limit_Viewers,
    On_Channel
)

def parts_in_order(mpm:Message_Part_Manager) -> Iterable[Message_Part]:
    for tpe in PART_ORDER:
        if tpe in mpm.keys():
            yield mpm[tpe]