from typing import TYPE_CHECKING, Callable, Literal, Optional, Sequence, TypeVar, override

from game.components.send.option import Option
from game.components.send.old_message import Old_Message, _Old_Message
from utils.emoji_groups import NO_YES_EMOJI
from utils.grammar import wordify_iterable
from utils.types import ChannelId, InteractionId, MessageId, PlayersIds

if TYPE_CHECKING:
    ...
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


def make_bullet_points(contents:list[str],emojis:Sequence[str]) -> list[Option]:
    """turns lists of texts and emojis into a list of bullet_points with the corresponding values"""
    to_return:list[Option] = []
    for i in range(len(contents)):
        to_return.append(
            Option(
                text = contents[i],
                emoji = emojis[i]
            )
        )
    return to_return
def make_no_yes_bullet_points() -> list[Option]:
    return make_bullet_points(['no','yes'],NO_YES_EMOJI)

class Child_Message(_Old_Message):
    def __init__(self,parent_message:'_Old_Message'):
        self.parent_message = parent_message
        self.parent_message.children.append(self)
        self.children:list[_Old_Message] = []

class Alias_Message(Child_Message):
    """creates a child message where the properties are determined from called functions"""
    def __init__(
            self,parent_message:'_Old_Message',
            content_modifier:OptionalModifier[str] = do_not_modify,
            attach_paths_modifier:OptionalModifier[list[str]] = do_not_modify,
            channel_id_modifier:OptionalModifier[ChannelId] = do_not_modify,
            message_id_modifier:OptionalModifier[MessageId] = do_not_modify,
            players_who_can_see_modifier:OptionalModifier[PlayersIds] = do_not_modify,
            bullet_points_modifier:OptionalModifier[list[Option]] = do_not_modify,
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
        return self.content_modifier(self.parent_message.text)
    @property
    @override
    def attach_paths(self) -> list[str] | None:
        return self.attach_paths_modifier(self.parent_message.attach_files)
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
        return self.players_who_can_see_modifier(self.parent_message.limit_players_who_can_see)
    @property
    @override
    def bullet_points(self) -> list[Option] | None:
        return self.bullet_points_modifier(self.parent_message.with_options)
    @property
    @override
    def reply_to_id(self) -> InteractionId|MessageId|None:
        return self.reply_to_id_mnodifier(self.parent_message.reference_message)
class Unique_Id_Alias_Message(Alias_Message):
    """creates an alias message capable of having its message_id set independantly of it's parent's message_id"""
    def __init__(self,parent_message:'Old_Message',
            content_modifier:OptionalModifier[str] = do_not_modify,
            attach_paths_modifier:OptionalModifier[list[str]] = do_not_modify,
            channel_id_modifier:OptionalModifier[ChannelId] = do_not_modify,
            players_who_can_see_modifier:OptionalModifier[PlayersIds] = do_not_modify,
            bullet_points_modifier:OptionalModifier[list[Option]] = do_not_modify):
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
            self,parent_message:'Old_Message',
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
    def __init__(self,parent_message:'Old_Message'):
        def add_bullet_points(content:Optional[str]) -> str:
            if content is None:
                content = ""
            else:
                content += "\n"
            if parent_message.with_options is None:
                bp = ""
            else:
                bp = wordify_iterable(str(bp) for bp in parent_message.with_options)
            return f"{content}{bp}"
        Alias_Message.__init__(self,parent_message,add_bullet_points)
            
class Reroute_Message(Alias_Message):
    """creates an alias message rerouting a message's channel to a new one"""
    def __init__(self,message:Old_Message,channel_id:ChannelId):
        Alias_Message.__init__(self,message,channel_id_modifier=lambda channel: channel_id)
