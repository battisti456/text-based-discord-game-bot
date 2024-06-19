from random import shuffle
from typing import Awaitable, Callable, Iterable, Optional, override

import discord
import discord.types
import discord.types.emoji

from time import time

from discord_interface.discord_sender import Discord_Sender
from discord_interface.common import Discord_Message, CompatibleChannels

from game import get_logger
from game.components.game_interface import (
    Game_Interface,
)
from game.components.send import Interaction, Address
from game.components.send.interaction import Send_Text
from utils.types import ChannelId, PlayerId

from utils.types import Grouping

type AsyncCallback = Callable[[],Awaitable[None]]

logger = get_logger(__name__)

class Discord_Game_Interface(Game_Interface):
    def __init__(self,channel_id:ChannelId,players:list[PlayerId]):
        Game_Interface.__init__(self)
        self.channel_id = channel_id
        self.players = players
        
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        self.client = discord.Client(intents = intents)
        self.default_sender = Discord_Sender(self)

        self.first_initialization = True
        self.on_start_callbacks:list[AsyncCallback] = []

        self.who_can_see_dict:dict[frozenset[PlayerId],ChannelId] = {}
        #region 
        @self.client.event
        async def on_ready():#triggers when client is logged into discord
            if self.first_initialization:
                for callback in self.on_start_callbacks:
                    await callback()
                self.first_initialization = False
            else:
                await self.reconnect()
        @self.client.event
        async def on_message(payload:discord.Message):#triggers when client
            address:Address|None
            if payload.author.id not in self.players:
                return
            try:
                assert payload.reference is not None
                assert payload.reference.message_id is not None
                message = Discord_Message(
                    payload.reference.message_id,
                    payload.channel.id
                )
                assert message in self.default_sender.cached_addresses
                address = self.default_sender.cached_addresses[message]
            except AssertionError:
                address = None
            await self.interact(Interaction(
                at_address=address,
                with_sendable=None,
                by_player=payload.author.id,#type:ignore
                at_time=time(),
                content = Send_Text(payload.content)
            ))
        @self.client.event
        async def on_raw_message_edit(payload:discord.RawMessageUpdateEvent):
            if payload.cached_message is not None:
                await on_message(payload.cached_message)
        #endregion
    @override
    async def reset(self):
        await super().reset()
        await self.client.wait_until_ready()
        assert isinstance(self.channel_id,int)
        channel = self.client.get_channel(self.channel_id)
        assert isinstance(channel,discord.TextChannel)
        for thread in channel.threads:
            await thread.delete()
        self.who_can_see_dict = {}
        to_del = tuple(self.default_sender.cached_addresses.keys())
        for message in to_del:
            del self.default_sender.cached_addresses[message]
    async def reconnect(self):
        """this method is called by discord.py when we have gotten on_ready more than once to hopefully ensure the game remains functional"""
        logger.warning("reconnecting after discord service reconnect")
        logger.warning("attempting to fetch tracked messages")
        for message in self.default_sender.cached_addresses.keys():
            if message.message_id is None:
                continue#message has not yet been sent
            channel = self.client.get_channel(message.channel_id)
            assert isinstance(channel,CompatibleChannels)
            partial = await channel.fetch_message(message.message_id)
            try:
                await partial.fetch()
            except discord.NotFound:
                logger.error(f"failed to find message {message}")
            except discord.HTTPException:
                logger.error(f"failed to fetch message {message}")
    @override
    async def _new_channel(self, name: Optional[str], who_can_see: Optional[Iterable[PlayerId]]) -> ChannelId:
        assert isinstance(self.channel_id,int)
        main_channel = self.client.get_channel(self.channel_id)
        assert isinstance(main_channel,discord.TextChannel)
        thread = None
        while thread is None:
            if name is None:
                name = ""
            await self.client.wait_until_ready()
            thread = await main_channel.create_thread(
                name = name,
                auto_archive_duration=10080#waits 7 days until it hides the thread
                )
        if who_can_see is not None:
            for player in who_can_see:
                assert isinstance(player,int)
                user = self.client.get_user(player)
                assert user is not None#user not found
                await self.client.wait_until_ready()
                await thread.add_user(user)
        return thread.id#type:ignore
    @override
    def get_players(self) -> frozenset[PlayerId]:
        players = self.players.copy()
        shuffle(players)
        return frozenset(players)
    def on_start(self,callback:AsyncCallback) -> AsyncCallback:
        self.on_start_callbacks.append(callback)
        return callback
    async def who_can_see_channel(self,players:Grouping[PlayerId]) -> ChannelId:
        """
        creates a ChannelId that only players can see, or returns one that it already made
        """
        fr_players = frozenset(players)
        channel_id:ChannelId
        if fr_players in self.who_can_see_dict:
            channel_id = self.who_can_see_dict[fr_players]
        else:
            channel_id = await self.new_channel(
                f"{self.default_sender.format_players(players)}'s Private Channel",
                players
            )
            self.who_can_see_dict[fr_players] = channel_id
        logger.info(f"channel limited game interface changing channel to id = {channel_id} so player_ids = {players} can see")
        return channel_id

        
        
