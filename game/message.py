from game import PlayerId, MessageId, ChannelId
from game.interaction import Interaction
from game.grammer import wordify_iterable

from math import ceil

from typing import Optional, Callable, TypeVar, Literal

ArgVar = TypeVar('ArgVar')
def do_not_modify(arg:ArgVar) -> ArgVar:
    return arg
def modify_nothing(arg:ArgVar) -> ArgVar|None:
    if isinstance(arg,list):
        new = arg.copy()
        new.clear()
        return new
    else:
        return None
OptionalModifier = Callable[[ArgVar|None],ArgVar|None]
Modifier = Callable[[ArgVar],ArgVar]
def keep(keep_value:bool) -> Modifier:
    if keep_value:
        return do_not_modify
    else:
        return modify_nothing


class Bullet_Point(object):
    def __init__(self,text:Optional[str] = None, emoji:Optional[str] = None):
        self.text = text
        self.emoji = emoji
    def __str__(self):
        return f"{self.emoji} (*{self.text}*)"

class Message(object):
    def __init__(
            self,content:Optional[str] = None,attach_paths:Optional[list[str]] = None,
            channel_id:Optional[ChannelId] = None,message_id:Optional[MessageId] = None,
            keep_id_on_copy:bool = False, players_who_can_see:Optional[list[PlayerId]] = None,
            bullet_points:Optional[list[Bullet_Point]] = None):
        self.content = content
        self.attach_paths = attach_paths
        self.channel_id = channel_id
        self.message_id = message_id
        self.keep_id_on_copy = keep_id_on_copy
        self.players_who_can_see = players_who_can_see
        self.bullet_points = bullet_points
        self.children:list[Message] = []
    def copy(self) -> 'Message':
        if self.keep_id_on_copy:
            message_id = self.message_id
        else:
            message_id = None
        return Message(self.content,self.attach_paths,self.channel_id,message_id,self.keep_id_on_copy,self.players_who_can_see)
    def is_sent(self) -> bool:
        return not self.message_id is None
    def is_response(self,interaction:Interaction,allow:Literal["original","aliases","children",'sub_aliases','sub_children'] = 'sub_children') -> bool:
        is_response = False
        is_response = is_response or interaction.reply_to_message_id == self.message_id
        if allow != 'original':
            if allow in ['aliases','children']:
                sub_text = 'original'
            else:
                sub_text = allow
            if allow in ['aliases','sub_aliases']:
                check = lambda child: isinstance(child,Alias_Message)
            else:
                check = lambda child: True
            is_response = is_response or any(child.is_response(interaction,sub_text) for child in self.children if check(child))
        return is_response

    def split(
            self,deliminator:Optional[str] = None,length:Optional[int] = None,
            add_start = "", add_end = "",
            add_join_start = "", add_join_end = "", rest_at_start:bool = False, rest_at_end:bool = True) -> list['Content_Split_Message']:
        if self.content is None:
            return [Content_Split_Message(self,0,0,add_start,add_end,True)]
        splits = []
        if not deliminator is None:
            found_index = self.content.find(deliminator)
            while found_index != -1:
                splits.append(found_index)
                found_index = self.content.find(deliminator,found_index)
        splits = [0] + splits + [len(self.content)]
        if not length is None:
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

class Child_Message(Message):
    def __init__(self,parent_message:'Message'):
        self.parent_message = parent_message
        self.parent_message.children.append(self)

class Alias_Message(Child_Message):
    def __init__(
            self,parent_message:'Message',
            content_modifier:OptionalModifier[str] = do_not_modify,
            attach_paths_modifier:OptionalModifier[list[str]] = do_not_modify,
            channel_id_modifier:OptionalModifier[ChannelId] = do_not_modify,
            message_id_modifier:OptionalModifier[MessageId] = do_not_modify,
            players_who_can_see_modifier:OptionalModifier[list[PlayerId]] = do_not_modify,
            bullet_points_modifier:OptionalModifier[list[Bullet_Point]] = do_not_modify):
        Child_Message.__init__(self,parent_message)
        self.content_modifier = content_modifier
        self.attach_paths_modifier = attach_paths_modifier
        self.channel_id_modifier = channel_id_modifier
        self.message_id_modifier = message_id_modifier
        self.players_who_can_see_modifier = players_who_can_see_modifier
        self.bullet_points_modifier = bullet_points_modifier
    @property
    def content(self) -> str | None:
        return self.content_modifier(self.parent_message.content)
    @property
    def attach_paths(self) -> list[str] | None:
        return self.attach_paths_modifier(self.parent_message.attach_paths)
    @property
    def channel_id(self) -> ChannelId | None:
        return self.channel_id_modifier(self.parent_message.channel_id)
    @property
    def message_id(self) -> MessageId | None:
        return self.message_id_modifier(self.parent_message.message_id)
    @message_id.setter
    def message_id(self,message_id:MessageId):
        self.parent_message.message_id = message_id
    @property
    def players_who_can_see(self) -> list[PlayerId] | None:
        return self.players_who_can_see_modifier(self.parent_message.players_who_can_see)
    @property
    def bullet_points(self) -> list[Bullet_Point] | None:
        return self.bullet_points_modifier(self.parent_message.bullet_points)
class Unique_Id_Alias_Message(Alias_Message):
    def __init__(self,parent_message:'Message',
            content_modifier:OptionalModifier[str] = do_not_modify,
            attach_paths_modifier:OptionalModifier[list[str]] = do_not_modify,
            channel_id_modifier:OptionalModifier[ChannelId] = do_not_modify,
            players_who_can_see_modifier:OptionalModifier[list[PlayerId]] = do_not_modify,
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
    def __init__(
            self,parent_message:'Message',
            start_index:int, end_index:int,
            add_start:str = "",
            add_end:str = "",
            include_rest:bool = False):
        def index_content(content:Optional[str]) -> str | None:
            if not content is None:
                return f"{add_start}{content[start_index:end_index]}{add_end}"
        Unique_Id_Alias_Message.__init__(
            self,parent_message,
            content_modifier=index_content,
            attach_paths_modifier=keep(include_rest),
            bullet_points_modifier=keep(include_rest)
            )
    
class Add_Bullet_Points_To_Content_Alias_Message(Alias_Message):
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
            
                
