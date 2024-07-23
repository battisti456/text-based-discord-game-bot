from random import shuffle
from typing import Awaitable, Callable, Iterable, Optional, override

import discord
import discord.types
import discord.types.emoji

from time import time

from discord_interface.discord_sender import Discord_Sender
from discord_interface.common import Discord_Message, CompatibleChannels, Discord_Address, Discord_Player

from utils.logging import get_logger
from game.components.game_interface import (
    Game_Interface,
)
from game.components.participant import Player, name_participants
from game.components.send import Interaction, Address
from game.components.send.interaction import Send_Text, Command
from game.components.send import sendables

from utils.common import get_first
from utils.types import Grouping
from config.discord_config import discord_config
from config.config import config

type AsyncCallback = Callable[[],Awaitable[None]]

logger = get_logger(__name__)

THREAD_MESSAGE_EXPIRATION = 60

class Discord_Game_Interface(Game_Interface):
    def __init__(self,channel_id:int,player_ids:list[int]):
        Game_Interface.__init__(self)
        self.channel_id = channel_id
        
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        self.client = discord.Client(intents = intents)
        self.default_sender = Discord_Sender(self)

        self.players:list[Discord_Player] = []

        self.first_initialization = True
        self.on_start_callbacks:list[AsyncCallback] = []

        self.who_can_see_dict:dict[frozenset[Player],int] = {}

        self.last_thread_message:tuple[float,str,Discord_Address]|None = None
        #region 
        @self.client.event
        async def on_ready():#triggers when client is logged into discord
            if self.first_initialization:
                for player_id in player_ids:
                    self.players.append(await Discord_Player.make(
                        client = self.client,
                        channel_id=channel_id,
                        id=player_id
                    ))
                for callback in self.on_start_callbacks:
                    await callback()
                self.first_initialization = False
            else:
                await self.reconnect()
        @self.client.event
        async def on_message(payload:discord.Message):#triggers when client
            address:Address|None
            if payload.author.id in discord_config["command_ids"] and payload.content.startswith(config['command_prefix']):
                await self.interact(Interaction(
                    at_address=None,
                    with_sendable=None,
                    by_player=self.find_player(payload.author.id),
                    at_time=time(),
                    content=Command(payload.content)
                ))
                return
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
                by_player=self.find_player(payload.author.id),
                at_time=time(),
                content = Send_Text(payload.content)
            ))
        @self.client.event
        async def on_raw_message_edit(payload:discord.RawMessageUpdateEvent):
            if payload.cached_message is not None:
                await on_message(payload.cached_message)
        #endregion
    def find_player(self,player_id:int) -> Player:
        return get_first(player for player in self.players if player.id == player_id)
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
    async def _new_channel(self, name: Optional[str], who_can_see: Optional[Iterable[Player]]) -> int:
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
        #a hacky attempt to condense a lot of thread notifications if several are created within a certain time of each other
        t = time()
        if self.last_thread_message is None or t - self.last_thread_message[0] > THREAD_MESSAGE_EXPIRATION:
            text:str = f"<#{thread.id}>"
            address = await self.default_sender(sendables.Text_Only(text=text))
            self.last_thread_message = (t,text,address)
        else:
            text = self.last_thread_message[1] + f" <#{thread.id}>"
            await self.default_sender(sendables.Text_Only(text=text),self.last_thread_message[2])
            self.last_thread_message = (t,text,self.last_thread_message[2])
        
        return thread.id#type:ignore
    @override
    def get_players(self) -> frozenset[Player]:
        players = self.players.copy()
        shuffle(players)
        return frozenset(players)
    def on_start(self,callback:AsyncCallback) -> AsyncCallback:
        self.on_start_callbacks.append(callback)
        return callback
    async def who_can_see_channel(self,players:Grouping[Player]) -> int:
        """
        creates a ChannelId that only players can see, or returns one that it already made
        """
        fr_players = frozenset(players)
        channel_id:int
        if fr_players in self.who_can_see_dict:
            channel_id = self.who_can_see_dict[fr_players]
        else:
            channel_id = await self._new_channel(
                f"{name_participants(players)}'s Private Channel",
                players
            )
            self.who_can_see_dict[fr_players] = channel_id
        logger.info(f"channel limited game interface changing channel to id = {channel_id} so player_ids = {players} can see")
        return channel_id
