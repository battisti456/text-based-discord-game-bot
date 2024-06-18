from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from game import get_logger
from game.components.send.sendable import Sendable
from game.components.send.sendable.prototype_sendables import (
    Attach_Files,
    Reference_Message,
    Text,
    With_Options,
)

if TYPE_CHECKING:
    from game.components.send.option import Option
    from utils.types import ChannelId, InteractionId, MessageId, PlayersIds

logger = get_logger(__name__)

@dataclass(frozen=True)
class _Old_Message(Sendable, is_prototype = True):
    ...

def Old_Message(
    text:'Optional[str]' = None,
    attach_files:'Optional[list[str]]' = None,
    on_channel:'Optional[ChannelId]' = None,
    _1:'Optional[MessageId]' = None, 
    limit_players_who_can_see:'Optional[PlayersIds]' = None,
    with_options:'Optional[list[Option]]' = None,
    reference_message:'Optional[MessageId|InteractionId]' = None
) -> '_Old_Message':
    prototypes:'list[type[Sendable]]' = []
    kwargs:'dict[str,Any]' = {}
    if text is not None:
        prototypes.append(Text)
        kwargs['text'] = text
    if attach_files is not None:
        prototypes.append(Attach_Files)
        kwargs['attach_files'] = attach_files
    if with_options is not None:
        prototypes.append(With_Options)
        kwargs['with_options'] = with_options
    if reference_message is not None:
        prototypes.append(Reference_Message)
        kwargs['reference_message'] = reference_message
    if on_channel is not None:
        logger.warning(f"ignoring on_channel={on_channel}")
    if _1 is not None:
        logger.warning(f"ignoring message_id={_1}")
    if limit_players_who_can_see is not None:
        logger.warning(f"ignoring limit_players={limit_players_who_can_see}")
    @dataclass(frozen=True)
    class __Old_Message(_Old_Message,*prototypes):
        ...
    return __Old_Message(**kwargs)
    
