from game import PlayerId,PlayerDict
from game.sender import Sender
from game.message import Message, Alias_Message
from game.game_interface import Game_Interface
from game.interaction import Interaction
from game.grammer import wordify_iterable

from typing import Optional, Generic, Any, Callable, TypeVar, ParamSpec

import asyncio
DataType = TypeVar('DataType',str,int,dict)
type ResponseValidator[DataType] = Callable[[PlayerId,DataType|None],bool]
type Condition = dict[Player_Input,bool]

not_none:ResponseValidator[Any] = lambda player, data: not data is None
class Player_Input[DataType](object):
    def __init__(
            self,gi:Game_Interface,sender:Sender,players:Optional[list[PlayerId]] = None,
            response_validator:ResponseValidator[DataType] = not_none):
        self.gi = gi
        self.sender = sender
        if players is None:
            self.players = self.gi.get_players()
        else:
            self.players = players
        self.responses:PlayerDict[DataType] = {}
        for player in self.players:
            self.responses[player] = None
        self._receive_inputs = False
        self._response_validator:ResponseValidator[DataType] = response_validator
        self.status_message = Alias_Message(
            Message(),lambda content: self.response_status())
    def response_status(self) -> str:
        #returns text describing which players have not responded to this input
        player_text = self.sender.format_players(player for player in self.players if self._response_validator(player,self.responses[player]))
        if player_text:
            return f"Waiting for {player_text} to respond in this input."
        else:
            return "Not waiting for anyone to respond in this input."
    async def _setup(self):
        pass
    async def _unsetup(self):
        pass
    async def update_response_status(self):
        #to be called only one something has changed
        await self.sender(self.status_message)
    def recieved_responses(self) -> bool:
        #returns weather all responses in this input are no longer None
        return all(self._response_validator(player,self.responses[player]) for player in self.players)
    async def _run(self):
        pass
    async def wait_until_received_all(self):
        while not self.recieved_responses():
            pass
        self._receive_inputs = False
    async def run(self,await_task:Optional[asyncio.Task] = None) -> PlayerDict[DataType]:
        if await_task is None:
            await_task = asyncio.create_task(self.wait_until_received_all())
        await self._setup()
        self._receive_inputs = True
        _run = asyncio.create_task(self._run())
        await asyncio.wait([await_task])
        _run.cancel()
        await self._unsetup()
        return self.responses
class Player_Input_In_Response_To_Message[DataType](Player_Input):
    def __init__(
            self, gi:Game_Interface, sender :Sender, 
            players:Optional[list[PlayerId]] = None, response_validator:ResponseValidator[DataType] = not_none,
            message:Optional[Message] = None, allow_edits:bool = True):
        Player_Input[DataType].__init__(self,gi,sender,players,response_validator)
        if message is None:
            self.message:Message = Message("Respond here.",players_who_can_see=players)
        else:
            self.message:Message = message
        self.allow_edits:bool = allow_edits
    def allow_interaction(self,interaction:Interaction) -> bool:
        if interaction.player_id is None:
            return False
        return (self.message.is_response(interaction) and 
                interaction.player_id in self.players and
                self.allow_edits or self.responses[interaction.player_id] is None)
        
class Player_Text_Input(Player_Input_In_Response_To_Message):
    def __init__(
            self, gi:Game_Interface, sender :Sender, players:Optional[list[PlayerId]] = None, 
            response_validator:ResponseValidator[str] = not_none, message:Optional[Message] = None,
            allow_edits:bool = True):
        Player_Input_In_Response_To_Message[str].__init__(self,gi,sender,players,response_validator,message,allow_edits)
        self.allow_edits = allow_edits
    async def _setup(self):
        @self.gi.on_action('send_message',self)
        @self.gi.on_action('edit_message',self)
        async def on_message_action(interaction:Interaction):
            if self.allow_interaction(interaction):
                assert not interaction.player_id is None
                self.responses[interaction.player_id] = interaction.content
                await self.update_response_status()
        @self.gi.on_action('delete_message',self)
        async def on_delete_action(interaction:Interaction):
            if self.allow_interaction(interaction):
                assert not interaction.player_id is None
                self.responses[interaction.player_id] = None
                await self.update_response_status()
    async def _unsetup(self):
        self.gi.purge_actions(self)

class Player_Multiple_Input(Player_Input):
    def __init__(self, gi:Game_Interface,sender:Sender,players:Optional[list[PlayerId]] = None):
        Player_Input.__init__(self,gi,sender,players)
class Multiple_Player_Inputs(Player_Input[dict[Player_Input[Any],Any]]):
    def __init__(
            self,gi:Game_Interface,sender:Sender,
            player_inputs:list[Player_Input],
            conditions:Optional[list[Condition]] = None):
        Player_Input.__init__(self,gi,sender)
        self.player_inputs = player_inputs
        self.conditions:list[Condition] = []
        if conditions is None:
            self.conditions = [{player_input:True for player_input in self.player_inputs}]
        else:
            self.conditions = conditions
    def response_status(self) -> str:
        not_responded:set[PlayerId] = set()
        for player_input in self.player_inputs:
            not_responded.intersection_update(set(player for player in player_input.players if player_input.responses[player] is None))
        player_text = self.sender.format_players(not_responded)
        if player_text:
            return f"Waiting for {player_text} to respond amongst multiple inputs."
        else:
            return "Not waiting for anyone to respond amongst multiple inputs."
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
        for player in self.players:#---------add condition to protect for player inputs not alway containingthe same players
            self.responses[player] = {player_input:player_input.responses[player] for player_input in self.player_inputs}
        return self.responses