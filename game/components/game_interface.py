import os
from typing import Any, Optional, override

from config.config import config
from game import get_logger
from game.components.message import Limit_Viewers, Message, On_Channel, Reroute_Message, Message_Part
from game.components.sender import Sender
from utils.types import ChannelId, Grouping, PlayerId, SimpleFunc

logger = get_logger(__name__)


class Interface_Sender(Sender):
    """
    a sender intrinsically linked to the game interface;
    it stores all messages that pass by it
    """
    def __init__(self,gi:'Game_Interface'):
        Sender.__init__(self)
        self.gi = gi
    @override
    async def __call__(self,message:Message) -> Any:
        return await self._send(message)

class Game_Interface(object):
    """
    the interface through which Game objects can interact with the players;
    this is a base class meant to be overwritten
    """
    SUPPORTED_MESSAGE_PARTS:set[type[Message_Part]] = set()
    def __init__(self):
        self.watched_messages:list[Message] = []
        self.on_setup_funcs:list[SimpleFunc[Game_Interface]] = []
    def on_setup(self,func:SimpleFunc['Game_Interface']):
        self.on_setup_funcs.append(func)
    def watch(self,message:Message):
        self.watched_messages.append(message)
    def un_watch(self,message:Message):
        self.watched_messages.remove(message)
    @classmethod
    def supported_parts(cls,message:Message) -> set[Message_Part]:
        equivalent_supported = set()
        for part in message.values():
            equivalent_supported.update(part.comply_to(cls.SUPPORTED_MESSAGE_PARTS))
        equivalent_usable:set[Message_Part] = set()
        for tp in cls.SUPPORTED_MESSAGE_PARTS:
            try:
                equivalent_usable.add(tp.merge(equivalent_supported))
            except IndexError:
                ...#type not in message
        return equivalent_usable
    async def send(self,message:Message):
        logger.info(str(message))
    async def setup(self):
        for func in self.on_setup_funcs:
            a = func(self)
            if a is not None:
                await a
    async def reset(self):
        """
        clears all stored on_actions and messages
        """
        logger.warning("resetting game interface")

        self.empty_temp()
    def empty_temp(self):
        """
        empties the temp folder of all files
        """
        for file in os.listdir(config['temp_path']):
            logger.debug(f"deleting '{config['temp_path']}/{file}'")
            os.unlink(f"{config['temp_path']}/{file}")
    def get_players(self) -> frozenset[PlayerId]:
        """
        gets relaxant players for Game object, should be randomized in order;
        should be implemented in child classes
        """
        return frozenset()
    async def _new_channel(self,name:Optional[str],who_can_see:Optional[Grouping[PlayerId]]) -> ChannelId:
        ...
    async def new_channel(self,name:Optional[str] = None, who_can_see:Optional[Grouping[PlayerId]] = None) -> ChannelId:
        """
        returns the ChannelId of a channel
        
        name: if specified, titles the channel with it
        
        who_can_see: if specified, only these players have access to the channel, if not specified should assume all players
        """
        channel_id:ChannelId = await self._new_channel(name,who_can_see)
        logger.info(f"created new channel with name = {name}, player_ids = {who_can_see}, channel_id = {channel_id}")
        return channel_id

class Channel_Limited_Interface_Sender(Interface_Sender): 
    """
    a subclass of Interface_Sender geared towards Channel_Limited_Game_Interfaces;
    it reroute's messages based on players_who_can see to make up for an interface which is unable to limit seeing messages to specific viewers directly
    """
    def __init__(self,gi:'Channel_Limited_Game_Interface'):
        Interface_Sender.__init__(self,gi)
    @override
    async def __call__(self,message:Message):
        if message.has(Limit_Viewers) and not message.has(On_Channel):
            assert isinstance(self.gi,Channel_Limited_Game_Interface)
            message= Reroute_Message(
                message,
                await self.gi.who_can_see_channel(message[Limit_Viewers].players)
            )
        return await Interface_Sender.__call__(self,message)

class Channel_Limited_Game_Interface(Game_Interface):
    """
    a subclass of Game_Interface that creates channels and reroutes messages for complying to Message.who_can_see
    """
    def __init__(self):
        Game_Interface.__init__(self)
        self.who_can_see_dict:dict[frozenset[PlayerId],ChannelId] = {}
        self.default_sender = Channel_Limited_Interface_Sender(self)
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


