from typing import TYPE_CHECKING, Callable, Literal, Optional, Sequence, TypeVar, override, Iterable

from utils.emoji_groups import NO_YES_EMOJI
from utils.types import ChannelId, InteractionId, MessageId, PlayersIds
from game.components.message.message_part import Message_Part
from game.components.message.content import Message_Text
if TYPE_CHECKING:
    from game.components.interaction import Interaction
    

type MessageSearchStrictness = Literal["original","aliases","children",'sub_aliases','sub_children']

ArgVar = TypeVar('ArgVar')
def do_not_modify(arg:ArgVar) -> ArgVar:
    """modifier for changing nothing"""
    return arg
def modify_into_nothing(arg:ArgVar) -> ArgVar|None:
    """modifier for a value to be empty if a list, or None if not"""
    if isinstance(arg,list):
        new = arg.copy()
        new.clear()
        return new
    else:
        return None
OptionalModifier = Callable[[ArgVar|None],ArgVar|None]
Modifier = Callable[[ArgVar],ArgVar]
def keep(keep_value:bool) -> Modifier:
    """returns do_not_modify if keep, and modify_into_nothing if not"""
    if keep_value:
        return do_not_modify
    else:
        return modify_into_nothing


class Bullet_Point(object):
    """a basic object storing the text and the emoji representations of a bullet point item"""
    def __init__(self,text:Optional[str] = None, emoji:Optional[str] = None):
        self.text = text
        self.emoji = emoji
    @override
    def __str__(self):
        return f"{self.emoji} (*{self.text}*)"

class Message(object):
    """
    an object storing all the values which can be included in a message from the bot to the players, meant to be sent with a sender; all values are optional

    content: the text content of the message

    attach_paths: a list of sting paths directing to files to be attatched to the message

    channel_id: the channel on which to send the message, if None will be assigned by sender to some dafault when sent

    message_id: the id of the message to edit, if None will be set by sender once sent

    players_who_can_see: the list of players who are permitted to see the message, if None all players can see

    bullet_points: a list of BulletPoint objects to display in the message
    """
    def __init__(
            self,
            content:str|Message_Part|Iterable[Message_Part] = [],
            channel_id:Optional[ChannelId] = None,
            message_id:Optional[MessageId] = None, 
            players_who_can_see:Optional[PlayersIds] = None,
            reply_to_id:Optional[MessageId|InteractionId] = None):
        self.parts:set[Message_Part] = set()
        if isinstance(content,str):
            Message_Text(content)
        elif isinstance(content,Message_Part):
            content.bind(self)
        else:
            for part in content:
                part.bind(self)
        self.channel_id = channel_id
        self.message_id = message_id
        self.players_who_can_see = players_who_can_see
        self.reply_to_id = reply_to_id
        self.children:list[Message] = []
    def is_sent(self) -> bool:
        """return weather or not this Message object refers to an already sent message"""
        return self.message_id is not None
    def is_response(self,interaction:'Interaction',allow:MessageSearchStrictness = 'sub_children') -> bool:
        """
        returns whether an interaction refers to this message with its reply_to_message_id
        
        allow: sets the strictness of the allowance parameters
            'original' only if this message has that id
            'aliases' only if this message or any child aliases have that id
            'children' only if this message or any children have that id
            'sub_aliases' only if this message or any of its alias decendants have that id
            'sub_children' whether this message or any of its descendants have that id
        """
        if interaction.reply_to_message_id is None:
            return False
        return self.is_message(interaction.reply_to_message_id,allow)
    def is_message(self,message_id:MessageId,allow:MessageSearchStrictness='sub_children') -> bool:
        """
        returns whether this message is referred to by the given MessageId
        
        allow: sets the strictness of the allowance parameters
            'original' only if this message has that id
            'aliases' only if this message or any child aliases have that id
            'children' only if this message or any children have that id
            'sub_aliases' only if this message or any of its alias descendants have that id
            'sub_children' whether this message or any of its descendants have that id
        """
        is_response = False
        is_response = is_response or message_id == self.message_id
        if allow != 'original':
            if allow in ['aliases','children']:
                sub_text = 'original'
            else:
                sub_text = allow
            def check(child):
                if allow in ['sub_aliases','sub_aliases']: 
                    return isinstance(child,Alias_Message)
                else:
                    return True
            is_response = is_response or any(child.is_message(message_id,sub_text) for child in self.children if check(child))
        return is_response
    def reply(self,content:str) -> 'Message':
        return Message(
            content = content,
            channel_id=self.channel_id,
            reply_to_id=self.message_id
        )
    @override
    def __hash__(self) -> int:
        return hash((self.message_id,self.channel_id))

def make_bullet_points(contents:list[str],emojis:Sequence[str]) -> list[Bullet_Point]:
    """turns lists of texts and emojis into a list of bullet_points with the corresponding values"""
    to_return:list[Bullet_Point] = []
    for i in range(len(contents)):
        to_return.append(
            Bullet_Point(
                text = contents[i],
                emoji = emojis[i]
            )
        )
    return to_return
def make_no_yes_bullet_points() -> list[Bullet_Point]:
    return make_bullet_points(['no','yes'],NO_YES_EMOJI)

class Child_Message(Message):
    def __init__(self,parent_message:'Message'):
        self.parent_message = parent_message
        self.parent_message.children.append(self)
        self.children:list[Message] = []

class Alias_Message(Child_Message):
    """creates a child message where the properties are determined from called functions"""
    def __init__(
            self,
            parent_message:'Message',
            parts_modifier:Modifier[set[Message_Part]] = do_not_modify,
            channel_id_modifier:OptionalModifier[ChannelId] = do_not_modify,
            message_id_modifier:OptionalModifier[MessageId] = do_not_modify,
            players_who_can_see_modifier:OptionalModifier[PlayersIds] = do_not_modify,
            reply_to_id_modifier:OptionalModifier[MessageId|InteractionId] = do_not_modify):
        Child_Message.__init__(self,parent_message)
        self.parts_modifier = parts_modifier
        self.channel_id_modifier = channel_id_modifier
        self.message_id_modifier = message_id_modifier
        self.players_who_can_see_modifier = players_who_can_see_modifier
        self.reply_to_id_modifier = reply_to_id_modifier
    @property
    @override
    def parts(self) -> set[Message_Part]:#type:ignore
        return self.parts_modifier(self.parent_message.parts)
    @property
    @override
    def channel_id(self) -> ChannelId | None:
        return self.channel_id_modifier(self.parent_message.channel_id)
    @property
    @override
    def message_id(self) -> MessageId | None:
        return self.message_id_modifier(self.parent_message.message_id)
    @message_id.setter
    def message_id(self,message_id:MessageId):
        self.parent_message.message_id = message_id
    @property
    @override
    def players_who_can_see(self) -> PlayersIds | None:
        return self.players_who_can_see_modifier(self.parent_message.players_who_can_see)
    @property
    @override
    def reply_to_id(self) -> InteractionId|MessageId|None:
        return self.reply_to_id_modifier(self.parent_message.reply_to_id)


class Reroute_Message(Alias_Message):
    """creates an alias message rerouting a message's channel to a new one"""
    def __init__(self,message:Message,channel_id:ChannelId):
        Alias_Message.__init__(self,message,channel_id_modifier=lambda channel: channel_id)
