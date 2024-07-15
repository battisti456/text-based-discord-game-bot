from typing import Awaitable, Callable, Hashable, Optional, Any
import os
from inspect import iscoroutinefunction
from functools import wraps

from utils.logging import get_logger
from game.components.participant import Player
from game.components.send import Sender, Interaction, InteractionCallback, Response, InteractionFilter, no_filter
from utils.types import ChannelId, Grouping
from config.config import config

logger = get_logger(__name__)


class Game_Interface(object):
    """
    the interface through which Game objects can interact with the players;
    this is a base class meant to be overwritten
    """
    def __init__(self):
        self.actions:dict[Any,set[InteractionCallback]] = {}
        self.default_sender = Sender()
    def watch(self,filter:InteractionFilter = no_filter,owner:Any = None):
        def decorator(func:InteractionCallback):
            if iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(interaction:Interaction) -> Response|None:
                    if filter(interaction):
                        return func(interaction)#type:ignore
                if owner not in self.actions.keys():
                    self.actions[owner] = set()
                self.actions[owner].add(async_wrapper)
                return async_wrapper
            else:
                @wraps(func)
                def wrapper(interaction:Interaction) -> Response|None:
                    if filter(interaction):
                        return func(interaction)#type:ignore
                if owner not in self.actions.keys():
                    self.actions[owner] = set()
                self.actions[owner].add(wrapper)
                return wrapper
        return decorator
    async def interact(self,interaction:Interaction) -> tuple[Response,...]:
        responses = []
        for action_set in tuple(self.actions.values()):
            for action in action_set:
                if iscoroutinefunction(action):
                    val = await action(interaction)
                else:
                    val = action(interaction)
                if isinstance(val,Awaitable):
                    val = await val
                if val is not None:
                    responses.append(val)
        return tuple(responses)
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
        owners = list(self.actions.keys())
        for owner in owners:
            self.purge_actions(owner)
    def purge_actions(self, owner:Hashable = None):
        """
        removes all on_actions corresponding to the given owner, which should have been registered when the action was;
        
        owner: can be of any type that is hashable, and is merely used for locating the action for purgeing
        """
        del self.actions[owner]
    def get_sender(self) -> Sender:
        """
        returns the default sender
        """
        return self.default_sender
    def get_players(self) -> frozenset[Player]:
        """
        gets relevant players for Game object, should be randomized in order;
        should be implemented in child classes
        """
        return frozenset()
    async def _new_channel(self,name:Optional[str],who_can_see:Optional[Grouping[Player]]) -> ChannelId:
        raise NotImplementedError()
    async def new_channel(self,name:Optional[str] = None, who_can_see:Optional[Grouping[Player]] = None) -> ChannelId:
        """
        returns the ChannelId of a channel
        
        name: if specified, titles the channel with it
        
        who_can_see: if specified, only these players have access to the channel, if not specified should assume all players
        """
        channel_id:ChannelId = await self._new_channel(name,who_can_see)
        logger.info(f"created new channel with name = {name}, player_ids = {who_can_see}, channel_id = {channel_id}")
        return channel_id
