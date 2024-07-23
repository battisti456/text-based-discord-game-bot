import os
from dataclasses import dataclass
from typing import Any, Hashable

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

@dataclass
class TriggerStat():
    attempts:int = 0
    triggers:int = 0
    filtered:int = 0
    def add(self,success:bool):
        self.attempts += 1
        if success:
            self.triggers += 1
        else:
            self.filtered += 1

class Game_Interface(object):
    """
    the interface through which Game objects can interact with the players;
    this is a base class meant to be overwritten
    """
    def __init__(self):
        self.actions:dict[Any,set[tuple[InteractionFilter[Any],InteractionCallback]]] = {}
        self.default_sender = Sender()
        self.im:Input_Maker = Input_Maker(self)
    def watch(self,filter:InteractionFilter[Any] = no_filter,owner:Any = None):
        def decorator(func:InteractionCallback):
            if owner not in self.actions.keys():
                self.actions[owner] = set()
            self.actions[owner].add((filter,func))
            return func
        return decorator
    async def interact(self,interaction:Interaction) -> tuple[Response,...]:
        responses = []
        self.triggers:dict[Hashable,TriggerStat] = {}
        for owner,filter_callbacks in tuple(self.actions.items()):
            self.triggers[owner] = TriggerStat()
            for filter,callback in filter_callbacks:
                success = filter(interaction)
                self.triggers[owner].add(success)
                if not success:
                    continue
                val = callback(interaction)
                try:
                    val = await val#type:ignore
                except TypeError:
                    ...
                if val is not None:
                    responses.append(val)
        logger.debug(str(self.triggers))
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
