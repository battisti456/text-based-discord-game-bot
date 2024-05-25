from math import ceil
from typing import TYPE_CHECKING, Callable, Literal, Optional, Sequence, TypeVar, override

from utils.emoji_groups import NO_YES_EMOJI
from utils.grammar import wordify_iterable
from utils.types import ChannelId, InteractionId, MessageId, PlayersIds

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
            self,content:Optional[str] = None,attach_paths:Optional[list[str]] = None,
            channel_id:Optional[ChannelId] = None,message_id:Optional[MessageId] = None, 
            players_who_can_see:Optional[PlayersIds] = None,
            bullet_points:Optional[list[Bullet_Point]] = None,
            reply_to_id:Optional[MessageId|InteractionId] = None):
        self.content = content
        self.attach_paths = attach_paths
        self.channel_id = channel_id
        self.message_id = message_id
        self.players_who_can_see = players_who_can_see
        self.bullet_points = bullet_points
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
        returns whether this message is refferd to by the given MessageId
        
        allow: sets the strictness of the allowance parameters
            'original' only if this message has that id
            'aliases' only if this message or any child aliases have that id
            'children' only if this message or any children have that id
            'sub_aliases' only if this message or any of its alias decendants have that id
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
    def split(
            self,deliminator:Optional[str] = None,length:Optional[int] = None,
            add_start = "", add_end = "",
            add_join_start = "", add_join_end = "", rest_at_start:bool = False, rest_at_end:bool = True) -> list['Content_Split_Message']:
        """
        returns a list of Content_Split_Messages based on splitting parameters; each Content_Split_Message will have content of a poriton of this Messages content

        deliminator: if given, what string to split the message's content on

        length: max length a split message's content can have

        add_start: content to add to the beggining of the first split message (not considered in length)

        add_end: content to add to the end of the last split message (not considered in length)

        add_join_start: content to add at the beggining of each split message, except the first (not considered in length)

        add_join_end: content to add to the end of each split message, except the last (not considered in length)

        rest_at_start: whether to include non-content paramaters of this message in the first split message

        rest_at_end: whether to include non-content parameters of this message in the last split message
        """
        if self.content is None:
            return [Content_Split_Message(self,0,0,add_start,add_end,True)]
        splits = []
        if deliminator is not None:
            found_index = self.content.find(deliminator)
            while found_index != -1:
                splits.append(found_index)
                found_index = self.content.find(deliminator,found_index)
        splits = [0] + splits + [len(self.content)]
        if length is not None:
            for i in range(len(splits)-1,0,-1):
                chars_in_segment = splits[i] - splits[i-1]
                if chars_in_segment > length:
                    num_divisions = ceil(chars_in_segment/length)
                    for j in range(num_divisions-2,0,-1):
                        splits.insert(i,splits[i-1] + j*chars_in_segment)
        to_return:list[Content_Split_Message] = []
        for i in range(len(splits)-1):
            start_text = add_join_start
            end_text = add_join_end
            include_rest= False
            if i == 0:
                start_text = add_start
                if rest_at_start:
                    include_rest = True
            if i == len(splits) -2:
                end_text = add_end
                if rest_at_end:
                    include_rest = True
            to_return.append(
                Content_Split_Message(
                    self,splits[i],splits[i+1],
                    start_text,end_text,include_rest
                )
            )
        return to_return
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
            self,parent_message:'Message',
            content_modifier:OptionalModifier[str] = do_not_modify,
            attach_paths_modifier:OptionalModifier[list[str]] = do_not_modify,
            channel_id_modifier:OptionalModifier[ChannelId] = do_not_modify,
            message_id_modifier:OptionalModifier[MessageId] = do_not_modify,
            players_who_can_see_modifier:OptionalModifier[PlayersIds] = do_not_modify,
            bullet_points_modifier:OptionalModifier[list[Bullet_Point]] = do_not_modify,
            reply_to_id_modifier:OptionalModifier[MessageId|InteractionId] = do_not_modify):
        Child_Message.__init__(self,parent_message)
        self.content_modifier = content_modifier
        self.attach_paths_modifier = attach_paths_modifier
        self.channel_id_modifier = channel_id_modifier
        self.message_id_modifier = message_id_modifier
        self.players_who_can_see_modifier = players_who_can_see_modifier
        self.bullet_points_modifier = bullet_points_modifier
        self.reply_to_id_mnodifier = reply_to_id_modifier
    @property
    @override
    def content(self) -> str | None:
        return self.content_modifier(self.parent_message.content)
    @property
    @override
    def attach_paths(self) -> list[str] | None:
        return self.attach_paths_modifier(self.parent_message.attach_paths)
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
    def bullet_points(self) -> list[Bullet_Point] | None:
        return self.bullet_points_modifier(self.parent_message.bullet_points)
    @property
    @override
    def reply_to_id(self) -> InteractionId|MessageId|None:
        return self.reply_to_id_mnodifier(self.parent_message.reply_to_id)
class Unique_Id_Alias_Message(Alias_Message):
    """creates an alias message capable of having its message_id set independantly of it's parent's message_id"""
    def __init__(self,parent_message:'Message',
            content_modifier:OptionalModifier[str] = do_not_modify,
            attach_paths_modifier:OptionalModifier[list[str]] = do_not_modify,
            channel_id_modifier:OptionalModifier[ChannelId] = do_not_modify,
            players_who_can_see_modifier:OptionalModifier[PlayersIds] = do_not_modify,
            bullet_points_modifier:OptionalModifier[list[Bullet_Point]] = do_not_modify):
        self.sub_message_id= None
        Alias_Message.__init__(
            self,parent_message,content_modifier,attach_paths_modifier,
            channel_id_modifier,lambda message_id: self.message_id,players_who_can_see_modifier,
            bullet_points_modifier)
    @Alias_Message.message_id.setter
    def message_id(self,message_id:MessageId):
        self.sub_message_id = message_id
class Content_Split_Message(Unique_Id_Alias_Message):
    """contains a subsection of the parent message's content as according to its split function"""
    def __init__(
            self,parent_message:'Message',
            start_index:int, end_index:int,
            add_start:str = "",
            add_end:str = "",
            include_rest:bool = False):
        def index_content(content:Optional[str]) -> str | None:
            if content is not None:
                return f"{add_start}{content[start_index:end_index]}{add_end}"
        Unique_Id_Alias_Message.__init__(
            self,parent_message,
            content_modifier=index_content,
            attach_paths_modifier=keep(include_rest),
            bullet_points_modifier=keep(include_rest)
            )
    
class Add_Bullet_Points_To_Content_Alias_Message(Alias_Message):
    """adds text representation of the bullet point list to the content as an alias"""
    def __init__(self,parent_message:'Message'):
        def add_bullet_points(content:Optional[str]) -> str:
            if content is None:
                content = ""
            else:
                content += "\n"
            if parent_message.bullet_points is None:
                bp = ""
            else:
                bp = wordify_iterable(str(bp) for bp in parent_message.bullet_points)
            return f"{content}{bp}"
        Alias_Message.__init__(self,parent_message,add_bullet_points)
            
class Reroute_Message(Alias_Message):
    """creates an alias message rerouting a message's channel to a new one"""
    def __init__(self,message:Message,channel_id:ChannelId):
        Alias_Message.__init__(self,message,channel_id_modifier=lambda channel: channel_id)
