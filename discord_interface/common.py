from typing import TypedDict, Sequence, Union
from dataclasses import dataclass, field
import uuid
from game.components.participant import Player

import discord

from game.components.send import Address

from smart_text import TextLike

from utils.logging import get_logger

logger = get_logger(__name__)


MESSAGE_MAX_LENGTH = 1800#actually 2000, but I leave extra for split indicators
SLEEP429 = 10
BLANK_TEXT = "--blank--"

class DiscordEditArgs(TypedDict, total = False):
    content:str
    embed:discord.Embed
    attachments:Sequence[discord.Attachment|discord.File]
    suppress:bool
    delete_after:float
    allowed_mentions:discord.AllowedMentions
    view:discord.ui.View
class DiscordSendArgs(TypedDict,total = False):
    content:str|None
    embed:discord.Embed
    files:Sequence[discord.File]
    delete_after:float
    allowed_mentions:discord.AllowedMentions
    reference:Union[discord.Message, discord.MessageReference, discord.PartialMessage]
    view:discord.ui.View
    silent:bool
def edit_to_send(kw_args:DiscordEditArgs) -> DiscordSendArgs:
    to_return:DiscordSendArgs = {}
    if 'content' in kw_args:
        to_return['content'] = kw_args['content']
    if 'embed' in kw_args:
        to_return['embed'] = kw_args['embed']
    if 'attachments' in kw_args:
        filtered = tuple(item for item in kw_args['attachments'] if isinstance(item,discord.File))
        if len(filtered) != kw_args['attachments']:
            logger.error(f"Discord attachments ignored in {kw_args['attachments']}")
        to_return['files'] = filtered
    if 'suppress' in kw_args:
        to_return['silent'] = kw_args['suppress']
    if 'delete_after' in kw_args:
        to_return['delete_after'] = kw_args['delete_after']
    if 'allowed_mentions' in kw_args:
        to_return['allowed_mentions'] = kw_args['allowed_mentions']
    if 'view' in kw_args:
        to_return['view'] = kw_args['view']
    return to_return


@dataclass(frozen=True)
class Discord_Message():
    message_id:int|None
    channel_id:int
    def set_message_id(self,message_id:int) -> 'Discord_Message':
        return Discord_Message(message_id,self.channel_id)

@dataclass(frozen=True)
class Discord_Address(Address):
    messages:list[Discord_Message] = field(hash=False,compare=False)
    id:uuid.UUID = field(default_factory=uuid.uuid4,init=False)

@dataclass(frozen=True)
class Discord_Player(Player):
    id:int = field(kw_only=True)
    @classmethod
    def make(cls,client:discord.Client,channel_id:int,id:int) -> 'Discord_Player':
        user = client.get_user(id)
        assert user is not None
        channel = client.get_channel(channel_id)
        assert isinstance(channel,CompatibleChannels)
        member = channel.guild.get_member(id)
        assert member is not None
        return Discord_Player(
            name = member.display_name,
            user_name = user.name,
            mention=user.mention,
            id=id
        )




def f(text:TextLike) -> str:
    return str(text)

CompatibleChannels = discord.TextChannel|discord.Thread