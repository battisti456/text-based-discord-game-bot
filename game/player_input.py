from game import PlayerId,PlayerDict,DataType
from game.sender import Sender
from game.message import Message
from game.game_interface import Game_Interface

from typing import Optional, Generic, Any

import asyncio

class Player_Input(Generic[DataType]):
    def __init__(self,gi:Game_Interface,sender:Sender,message:Message,players:Optional[list[PlayerId]] = None):
        self.gi = gi
        self.sender = sender
        self.message = message
        if players is None:
            self.players = self.gi.get_players()
        else:
            self.players = players
        self.responses:PlayerDict[DataType] = {}
        for player in self.players:
            self.responses[player] = None
        self._receive_inputs = False
    def recieved_responses(self) -> bool:
        return all(not self.responses[player] is None for player in self.players)
    async def setup_input(self):
        pass
    async def core_loop(self):
        pass
    async def unsetup_input(self):
        pass
    async def _run(self) -> PlayerDict[DataType]:
        return self.responses
    async def wait_until_received_all(self):
        while not self.recieved_responses():
            pass
        self._receive_inputs = False
    async def run(self) -> PlayerDict[DataType]:
        self._receive_inputs = True
        await asyncio.wait([
            asyncio.create_task(self._run()),
            asyncio.create_task(self.wait_until_received_all())])
        return self.responses
class Player_Text_Input(Player_Input):
    def __init__(self, gi:Game_Interface,sender:Sender,message:Message,players:Optional[list[PlayerId]] = None):
        Player_Input.__init__(self,gi,sender,message,players)
        self.responses:PlayerDict[str] = {}
class Player_Multiple_Input(Player_Input):
    def __init__(self, gi:Game_Interface,sender:Sender,message:Message,players:Optional[list[PlayerId]] = None):
        Player_Input.__init__(self,gi,sender,message,players)
Condition = dict[Player_Input,bool]
class Multiple_Player_Inputs(Player_Input[dict[Player_Input[Any],Any]]):
    def __init__(
            self,gi:Game_Interface,sender:Sender,message:Message,
            player_inputs:list[Player_Input],
            conditions:Optional[list[Condition]] = None):
        Player_Input.__init__(self,gi,sender,message)
        self.player_inputs = player_inputs
        self.conditions:list[Condition] = []
        if conditions is None:
            self.conditions = [{player_input:True for player_input in self.player_inputs}]
        else:
            self.conditions = conditions
    def recieved_responses(self) -> bool:
        inputs_done = {player_input:player_input.recieved_responses() for player_input in self.player_inputs}
        for condition in self.conditions:
            if all(inputs_done[player_input] or not condition[player_input] for player_input in self.player_inputs):
                return True
        return False
    async def _run(self) -> PlayerDict[dict[Player_Input,Any]]:
        tasks:list[asyncio.Task] = []
        for player_input in self.player_inputs:
            tasks.append(asyncio.create_task(player_input._run()))
        await asyncio.wait(tasks)
        for player in self.players:
            self.responses[player] = {player_input:player_input.responses[player] for player_input in self.player_inputs}
        return self.responses