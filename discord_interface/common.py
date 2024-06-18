from typing import TypedDict, Sequence
from dataclasses import dataclass

import discord

from game.components.send import Send_Address

from smart_text import TextLike


MESSAGE_MAX_LENGTH = 1800#actually 2000, but I leave extra for split indicators
SLEEP429 = 10
BLANK_TEXT = "--blank--"

class DiscordEditArgs(TypedDict, total = False):
    content:str|None
    embed:discord.Embed|None
    attachments:Sequence[discord.Attachment|discord.File]
    suppress:bool
    delete_after:float|None
    allowed_mentions:discord.AllowedMentions|None
    view:discord.ui.View|None

@dataclass(frozen=True)
class Discord_Message():
    message_id:int
    channel_id:int

@dataclass(frozen=True)
class Discord_Address(Send_Address):
    messages:list[Discord_Message]

def f(text:TextLike) -> str:
    return str(text)

CompatibleChannels = discord.TextChannel|discord.Thread