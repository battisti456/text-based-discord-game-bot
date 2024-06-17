from typing import Awaitable, Callable, Hashable, Optional
import os

from game import get_logger
from game.components.send import Sender
from game.components.interaction import INTERACTION_TYPES, Interaction, InteractionType
from utils.types import ChannelId, Grouping, PlayerId
from config.config import config

logger = get_logger(__name__)

type Action = Callable[[Interaction],Awaitable]


class Game_Interface(object):
    """
    the interface through which Game objects can interact with the players;
    this is a base class meant to be overwritten
    """
    def __init__(self):
        self.actions:dict[InteractionType,list[Action]] = {}
        self.action_owners:dict[Action,Hashable] = {}
        self.clear_actions()
        self.default_sender = Sender()

    async def reset(self):
        """
        clears all stored on_actions and messages
        """
        logger.warning("resetting game interface")
        self.clear_actions()
    def empty_temp(self):
        """
        empties the temp folder of all files
        """
        for file in os.listdir(config['temp_path']):
            logger.debug(f"deleting '{config['temp_path']}/{file}'")
            os.unlink(f"{config['temp_path']}/{file}")
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
    def get_sender(self) -> Sender:
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
        gets relevant players for Game object, should be randomized in order;
        should be implemented in child classes
        """
        return frozenset()
    async def _new_channel(self,name:Optional[str],who_can_see:Optional[Grouping[PlayerId]]) -> ChannelId:
        raise NotImplementedError()
    async def new_channel(self,name:Optional[str] = None, who_can_see:Optional[Grouping[PlayerId]] = None) -> ChannelId:
        """
        returns the ChannelId of a channel
        
        name: if specified, titles the channel with it
        
        who_can_see: if specified, only these players have access to the channel, if not specified should assume all players
        """
        channel_id:ChannelId = await self._new_channel(name,who_can_see)
        logger.info(f"created new channel with name = {name}, player_ids = {who_can_see}, channel_id = {channel_id}")
        return channel_id
