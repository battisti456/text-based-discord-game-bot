from game import PlayerId,MessageId,ChannelId,InteractionId
from typing import Optional, Literal, get_args

InteractionType = Literal[
    'send_message',
    'delete_message',
    'select_option',
    'deselect_option']
INTERACTION_TYPES = get_args(InteractionType)

class Interaction(object):
    """
    an object for storing the data generated by a players interaction with the interface
    
    each interaction follows a designated InteractionType, but it is up to the implemantation to actually store the relavant data
    """
    def __init__(self,interaction_type:InteractionType):
        self.player_id:Optional[PlayerId] = None
        self.interaction_id:Optional[InteractionId] = None
        self.channel_id:Optional[ChannelId] = None
        self.reply_to_message_id:Optional[MessageId] = None

        self.content:Optional[str] = None
        self.interaction_type:InteractionType = interaction_type

        self.choice_index:Optional[int] = None
        
