from typing import Any, Awaitable, Callable, Hashable, Optional, override

from game import get_logger
from game.components.interaction import INTERACTION_TYPES, Interaction, InteractionType
from game.components.message import Message, Reroute_Message
from game.components.sender import Sender
from game.utils.types import ChannelId, Grouping, MessageId, PlayerId

logger = get_logger(__name__)

type Action = Callable[[Interaction],Awaitable]

class Interface_Sender(Sender):
    """
    a sender intrinsicly linked to the game interface;
    it stores all messages that pass by it
    """
    def __init__(self,gi:'Game_Interface'):
        Sender.__init__(self)
        self.gi = gi
    @override
    async def __call__(self,message:Message) -> Any:
        self.gi.track_message(message)
        return await self._send(message)

class Game_Interface(object):
    """
    the interface through which Game objects can interact with the players;
    this is a base class meant to be overwritten
    """
    def __init__(self):
        self.actions:dict[InteractionType,list[Action]] = {}
        self.action_owners:dict[Action,Hashable] = {}
        self.clear_actions()
        self.default_sender = Interface_Sender(self)
        self.tracked_messages:list[Message] = []

    async def reset(self):
        """
        clears all stored on_actions and messages
        """
        logger.warning("resetting game interface")
        self.purge_tracked_messages()
        self.clear_actions()
    def track_message(self,message:Message):
        """
        adds a message to the interfaces tracked messages list
        """
        logger.info(f"tracking object with message_id = {message.message_id}")
        self.tracked_messages.append(message)
    def purge_tracked_messages(self):
        """
        empties the interfaces tracked messages list
        """
        logger.info(f"untracking all messages; message_id's in {list(message.message_id for message in self.tracked_messages)}")
        self.tracked_messages.clear()
    def find_tracked_message(self,message_id:MessageId) -> Message | None:
        """
        locates a Message object by the message's message_id if it can;
        returns None if there are no messages that identify with that MessageId;
        if there are multiple messages, the interface only returns the first it encounters
        """
        for message in self.tracked_messages:
            if message.is_message(message_id,'original'):
                return message
        return None
    def clear_actions(self):
        """
        clears all on_actions
        """
        logger.info(f"clearing all on_action events totalling {len(self.actions)}")
        for interaction_type in INTERACTION_TYPES:
            self.actions[interaction_type] = []
        self.action_owners = {}
    def purge_actions(self, owner:Hashable = None):
        """
        removes all on_actions corresponding to the given owner, which should have been registered when the action was;
        
        owner: can be of any type that is hashable, and is merely used for locating the action for purgeing
        """
        actions_to_purge:set[Action] = set(action for action in self.action_owners if self.action_owners[action] == owner)
        logger.info(f"clearing all on_action events owned by {owner} totalling {len(actions_to_purge)}")
        for action in actions_to_purge:
            for interaction_type in self.actions:
                while action in self.actions[interaction_type]:
                    self.actions[interaction_type].remove(action)
            del self.action_owners[action]
    def get_sender(self) -> Interface_Sender:
        """
        returns the default sender
        """
        return self.default_sender
    async def _trigger_action(
            self,interaction:Interaction):
        """
        called when the game interface notices a player input and decides it is an interaction;
        should be used in child classes
        """
        logger.info(f"interaction of type = {interaction.interaction_type} with interaction_id = {interaction.interaction_id} calling {len(list(self.actions[interaction.interaction_type]))} actions")
        for action in self.actions[interaction.interaction_type]:
            await action(interaction)
    def on_action(self,action_type:InteractionType,owner:Hashable = None) -> Callable[[Action],Action]:
        """
        stores the given function to be called on interactions matching the given interactiontype;
        returns a wrapper that stores the function, but does not change it
        
        owner: can be of any type that is hashable, and is merely used for locating the action for purgeing
        """
        def wrapper(func:Action) -> Action:
            logger.info(f"adding new action seeking interactions of type = {action_type}; owned by {owner}")
            self.actions[action_type].append(func)
            self.action_owners[func] = owner
            return func
        return wrapper
    def get_players(self) -> frozenset[PlayerId]:
        """
        gets relavant players for Game object, should be randomized in order;
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
    a subclass of Iterface_Sender geared towards Channel_Limited_Game_Interfaces;
    it reroute's messages based on players_who_can see to make up for an interface which is unable to limit seeing messions to specific viewers directly
    """
    def __init__(self,gi:'Channel_Limited_Game_Interface'):
        Interface_Sender.__init__(self,gi)
    @override
    async def __call__(self,message:Message):
        if (message.players_who_can_see is not None) and message.channel_id is None:
            assert isinstance(self.gi,Channel_Limited_Game_Interface)
            message= Reroute_Message(
                message,
                await self.gi.who_can_see_channel(message.players_who_can_see)
            )
        return await Interface_Sender.__call__(self,message)

class Channel_Limited_Game_Interface(Game_Interface):
    """
    a subclass of Game_Interface that creates channels and reroputes messages for complying to Message.who_can_see
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
        logger.info(f"channel limited game interface changing channel t o id = {channel_id} so player_ids = {players} can see")
        return channel_id


