import os
from functools import wraps
from inspect import iscoroutinefunction
from typing import Any, Awaitable, Hashable

from config.config import config
from game.components.input_ import Input_Maker
from game.components.participant import Player
from game.components.send import (
    Interaction,
    InteractionCallback,
    InteractionFilter,
    Response,
    Sender,
    no_filter,
)
from utils.logging import get_logger

logger = get_logger(__name__)


class Game_Interface(object):
    """
    the interface through which Game objects can interact with the players;
    this is a base class meant to be overwritten
    """
    def __init__(self):
        self.actions:dict[Any,set[InteractionCallback]] = {}
        self.default_sender = Sender()
        self.im:Input_Maker = Input_Maker(self)
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
