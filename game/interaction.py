from game import PlayerId,MessageId,ChannelId,InteractionId
from typing import Optional, Literal, get_args

InteractionType = Literal[
    'send_message',
    'edit_message',
    'delete_message',
    'select_option',
    'reselect_option',
    'deselect_option']
INTERACTION_TYPES = get_args(InteractionType)

class Interaction(object):
    def __init__(self,interaction_type:InteractionType):
        self.player_id:Optional[PlayerId] = None
        self.interaction_id:Optional[InteractionId] = None
        self.channel_id:Optional[ChannelId] = None
        self.reply_to_message_id:Optional[MessageId] = None

        self.content:Optional[str] = None
        self.interaction_type:InteractionType = interaction_type
        