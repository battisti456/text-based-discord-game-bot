from time import sleep, time
from typing import TYPE_CHECKING, override, Iterable

import discord

from discord_interface.common import (
    BLANK_TEXT,
    SLEEP429,
    CompatibleChannels,
    Discord_Address,
    Discord_Message,
    DiscordEditArgs,
    f,
)
from discord_interface.custom_views import One_Selectable_View, One_Text_Field_View
from game import get_logger
from game.components.send import Interaction, Interaction_Content, Sendable, Sender
from game.components.send.interaction import Select_Options
from game.components.send.old_message import _Old_Message
from game.components.send.sendable.prototype_sendables import (
    Attach_Files,
    Text,
    With_Options,
)
from game.components.send.sendable.sendables import Text_Only, Text_With_Options, Text_With_Text_Field
from utils.grammar import wordify_iterable

if TYPE_CHECKING:
    from discord_interface.discord_interface import Discord_Game_Interface
    from utils.types import ChannelId, PlayerId

logger = get_logger(__name__)

class Discord_Sender(Sender[Discord_Address]):
    def __init__(self,gi:'Discord_Game_Interface'):
        Sender.__init__(self)
        self.gi = gi
        self.client = gi.client
        self.default_channel = gi.channel_id
    @override
    async def generate_address(self, channel_id: 'ChannelId | None' = None, length:int = 1) -> 'Discord_Address':
        if channel_id is None:
            channel_id = self.default_channel
        assert isinstance(channel_id,int)
        channel = await self.client.fetch_channel(channel_id)
        assert isinstance(channel,CompatibleChannels)
        messages:list[Discord_Message] = []
        for _ in range(length):
            await self.client.wait_until_ready()
            discord_message:discord.Message = await channel.send(BLANK_TEXT)
            messages.append(Discord_Message(
                message_id=discord_message.id,
                channel_id=channel_id
            ))
        return Discord_Address(messages)
    async def extend_address(self,address:Discord_Address, num:int) -> Discord_Address:
        to_add = await self.generate_address(
            address.messages[-1].channel_id,#type:ignore
            num)
        for message in to_add.messages:
            address.messages.append(message)
        return address
    @override
    async def _send(self, sendable: Sendable, address: Discord_Address|None = None) -> Discord_Address:
        edit_kwargs:list[DiscordEditArgs] = []
        reactions:dict[int,list[discord.Emoji|discord.PartialEmoji|discord.Reaction]] = {}
        if isinstance(sendable,_Old_Message):
            ...
        elif isinstance(sendable,Text_Only):
            edit_kwargs.append({
                'content' : f(sendable.text)
            })
        elif isinstance(sendable,Text_With_Options):
            if address is None:
                address = await self.generate_address()
            edit_kwargs.append({
                'content' : f(sendable.text),
                'view' : One_Selectable_View(self.gi,address,sendable)
            })
        elif isinstance(sendable,Text_With_Text_Field):
            if address is None:
                address = await self.generate_address()
            edit_kwargs.append({
                'content' : f(sendable.text),
                'view' : One_Text_Field_View(self.gi,address,sendable)
            })
        else:#unknown type, just go by subtypes
            if isinstance(sendable,Text):
                ...
            if isinstance(sendable,With_Options):
                ...
            if isinstance(sendable,Attach_Files):
                ...
        num_to_extend:int = len(edit_kwargs) - (0 if address is None else len(address.messages))
        if address is None:
            address = await self.generate_address(length=num_to_extend)
        elif num_to_extend > 0:
            address = await self.extend_address(address,num_to_extend)
        for i,message in enumerate(address.messages):
            kwargs:DiscordEditArgs
            if i >= len(edit_kwargs):
                kwargs = {"content" : BLANK_TEXT}
            else:
                kwargs = edit_kwargs[i]
            channel = self.client.get_channel(message.channel_id)
            assert isinstance(channel,CompatibleChannels)
            partial_message = channel.get_partial_message(message.message_id)
            discord_message = await partial_message.fetch()
            await discord_message.edit(**kwargs)
            if i in reactions.keys():
                react = reactions[i]
                for emoji in react:
                    j:bool = False
                    while not j:
                        try:
                            await self.client.wait_until_ready()
                            await discord_message.add_reaction(emoji)
                            j = True
                        except Exception as e:
                            logger.error(f"failed to add bullet points due to:\n{type(e)}: {e}")
                            sleep(SLEEP429)
            

        return address
    async def _old_send(self, sendable: _Old_Message, address:Discord_Address):
        channel = self.client.get_channel(address.messages[0].channel_id)
        assert isinstance(channel,CompatibleChannels)
        attachments:list[discord.File] = []
        if isinstance(sendable,Attach_Files):
            for path in sendable.attach_files:
                attachments.append(discord.File(path))
        await self.client.wait_until_ready()
        discord_message:discord.Message = await channel.fetch_message(address.messages[0].message_id)
        await discord_message.edit(
            content=str(BLANK_TEXT if not isinstance(sendable,Text) else sendable.text),
            attachments=attachments
            )
        if isinstance(sendable,With_Options):
            for bp in sendable.with_options:
                if bp.emoji is not None:
                    emoji = discord.PartialEmoji(name = bp.emoji)
                    success = False
                    while not success:
                        try:
                            await self.client.wait_until_ready()
                            await discord_message.add_reaction(emoji)
                            success = True
                        except Exception as e:#not sure what the actual exceptions are
                            logger.error(f"failed to add bullet points due to:\n{type(e)}: {e}")
                            sleep(SLEEP429)
    @override
    def format_players_md(self, players: 'Iterable[PlayerId]') -> str:
        return wordify_iterable(f"<@{player}>" for player in players)
    @override
    def format_players(self,players:'Iterable[PlayerId]') -> str:
        player_names:list[str] = []
        for player in players:
            assert isinstance(player,int)
            user = self.client.get_user(player)
            if user is not None:
                player_names.append(user.display_name)
            else:
                player_names.append(str(player))
        return wordify_iterable(player_names)