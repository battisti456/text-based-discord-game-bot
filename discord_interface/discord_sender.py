from typing import TYPE_CHECKING, Hashable, Iterable, override

import discord

from discord_interface.common import (
    BLANK_TEXT,
    CompatibleChannels,
    Discord_Address,
    Discord_Message,
    DiscordEditArgs,
    edit_to_send,
    f,
    pre_process,
)
from discord_interface.custom_views import (
    Button_Select_View,
    One_Selectable_View,
    One_Text_Field_View,
    Options_And_Text_View,
)
from game.components.participant import ParticipantType, name_participants
from game.components.send import Sendable, Sender
from game.components.send.sendable.prototype_sendables import (
    Text,
    With_Options,
    With_Text_Field,
)
from game.components.send.sendable.sendables import (
    Attach_Files,
    Text_Only,
    Text_With_Options,
    Text_With_Options_And_Text_Field,
    Text_With_Text_Field,
)
from smart_text import TextLike
from utils.common import get_first
from utils.logging import get_logger

if TYPE_CHECKING:
    from discord_interface.discord_interface import Discord_Game_Interface

logger = get_logger(__name__)

class Discord_Sender(Sender[Discord_Address]):
    SUPPORTED_SENDABLES:tuple[type[Sendable],...] = (
        Text_Only,
        Text_With_Options,
        Text_With_Text_Field
    )
    SUPPORTED_PROTOTYPES:tuple[type[Sendable],...] = (
        Text,
        With_Options,
        With_Text_Field,
        Attach_Files
    )
    def __init__(self,gi:'Discord_Game_Interface'):
        Sender.__init__(self)
        self.gi = gi
        self.client = gi.client
        self.default_channel = gi.channel_id

        self.cached_addresses:dict[Discord_Message,Discord_Address] = {}
        self.threads:dict[Hashable,int] = {frozenset():self.default_channel}
    @override
    async def generate_address(
        self, 
        *args:Hashable,
        length:int = 1) -> 'Discord_Address':
        key = frozenset(args)
        if key not in self.threads.keys():
            name:TextLike|None = None
            try:
                name = get_first(val for val in key if isinstance(val,TextLike))
            except IndexError:
                ...
            participants:set[ParticipantType] = set()
            for val in key:
                if isinstance(val,ParticipantType):
                    participants.add(val)
                if isinstance(val,Iterable):
                    for p in val:
                        if isinstance(p,ParticipantType):
                            participants.add(p)
            if name is None:
                if len(participants) == 0:
                    name = "Private Channel"
                else:
                    name = name_participants(participants) +"'s private channel"
            thread_id = await self.gi._new_channel(name,participants)
            self.threads[key] = thread_id
        return Discord_Address(messages=list(Discord_Message(message_id=None,channel_id = self.threads[key]) for _ in range(length)), key = key)
    async def extend_address(self,address:Discord_Address, num:int):
        to_add = await self.generate_address(
            None if len(address.messages) == 0 else address.messages[-1].channel_id,#type:ignore
            length = num)
        for message in to_add.messages:
            self.cached_addresses[message] = address
            address.messages.append(message)
    @override
    async def _send(self, sendable: Sendable, address: Discord_Address|None = None) -> Discord_Address:
        if address is None:
            address = await self.generate_address()
        edit_kwargs:list[DiscordEditArgs] = []
        if isinstance(sendable,Text_Only):
            edit_kwargs.append({
                'content' : f(sendable.text)
            })
        elif isinstance(sendable,Text_With_Options):
            view:discord.ui.View
            if len(sendable.with_options) == 2 and sendable.max_selectable == 1:
                view = Button_Select_View(self.gi,address,sendable)
            else:
                view = One_Selectable_View(self.gi,address,sendable)
            edit_kwargs.append({
                'content' : f(sendable.text),
                'view' : view
            })
        elif isinstance(sendable,Text_With_Text_Field):
            edit_kwargs.append({
                'content' : f(sendable.text),
                'view' : One_Text_Field_View(self.gi,address,sendable)
            })
        elif isinstance(sendable,Text_With_Options_And_Text_Field):
            edit_kwargs.append({
                'content' : f(sendable.text),
                'view' : Options_And_Text_View(self.gi,address,sendable)
            })
        else:#unknown type, just go by subtypes
            unsupported = sendable.prototypes()-set(self.SUPPORTED_PROTOTYPES)
            if unsupported:
                logger.warning(f"Type of {sendable} not supported by {self}, attempting to send primitives but {unsupported} are not supported.")
            num_views:int = sum(int(isinstance(sendable,prototype)) for prototype in (
                With_Text_Field,
                With_Options
            ))
            if address is None:
                address = await self.generate_address(length=num_views)
            elif len(address.messages) < num_views:
                await self.extend_address(address,len(address.messages) - num_views)
            text = BLANK_TEXT
            if isinstance(sendable,Text):
                text = f(sendable.text)
            if isinstance(sendable,With_Options):
                edit_kwargs.append({
                    'content' : text,
                    'view' : One_Selectable_View(self.gi,address,sendable)
                })
            if isinstance(sendable,With_Text_Field):
                edit_kwargs.append({
                    'content' : text,
                    'view' : One_Text_Field_View(self.gi,address,sendable)
                })
            if isinstance(sendable,Attach_Files):
                edit_kwargs.append({
                    'content' : text,
                    'attachments' : list(discord.File(path) for path in sendable.attach_files)
                })
            if len(edit_kwargs) == 0:
                edit_kwargs.append({
                    'content' : text
                })
            
        num_to_extend:int = len(edit_kwargs) - (0 if address is None else len(address.messages))
        if address is None:
            address = await self.generate_address(length=num_to_extend)
        elif num_to_extend > 0:
            await self.extend_address(address,num_to_extend)
        assert address is not None
        for i in range(len(address.messages)):
            kwargs:DiscordEditArgs
            message = address.messages[i]
            if i >= len(edit_kwargs):
                kwargs = {}
            else:
                kwargs = edit_kwargs[i]
            channel = self.client.get_channel(message.channel_id)
            assert isinstance(channel,CompatibleChannels)
            if message.message_id is None:
                await self.client.wait_until_ready()
                discord_message = await channel.send(**edit_to_send(kwargs))
                address.messages[i] = message.set_message_id(discord_message.id)
                self.cached_addresses[address.messages[i]] = address
            else:
                partial_message = channel.get_partial_message(message.message_id)
                await self.client.wait_until_ready()
                discord_message = await partial_message.fetch()
                await self.client.wait_until_ready()
                await discord_message.edit(**pre_process(kwargs))
        return address