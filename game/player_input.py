from game import PlayerId,PlayerDict,PlayerDictOptional, make_player_dict
from game.sender import Sender
from game.message import Message, Alias_Message
from game.game_interface import Game_Interface
from game.interaction import Interaction
from game.response_validator import ResponseValidator, Validation, not_none

from typing import Optional, Any, Callable, Awaitable

import asyncio
type Condition = dict[Player_Input,bool]

SLEEP_TIME = 10

class Player_Input[T]():
    def __init__(
            self,name:str, gi:Game_Interface,sender:Sender,players:Optional[list[PlayerId]] = None,
            response_validator:ResponseValidator[T] = not_none, 
            who_can_see:Optional[list[PlayerId]] = None):
        self.name = name
        self.gi = gi
        self.sender = sender
        if players is None:
            self.players = self.gi.get_players()
        else:
            self.players = players
        self.responses:PlayerDictOptional[T] = make_player_dict(self.players,None)
        self._receive_inputs = False
        self._response_validator:ResponseValidator[T] = response_validator
        self.status_message = Alias_Message(
            Message(players_who_can_see=who_can_see),lambda content: self.response_status())
        self.funcs_to_call_on_update:list[Callable[[],Awaitable]] = []
    def on_update(self,func:Callable[[],Awaitable]) -> Callable[[],Awaitable]:
        self.funcs_to_call_on_update.append(func)
        return func
    def response_status(self) -> str:
        #returns text describing which players have not responded to this input
        validation:PlayerDict[Validation] = {player:self._response_validator(player,self.responses[player]) for player in self.players}
        players_not_responded = list(player for player in self.players if not validation[player][0])
        player_text = self.sender.format_players_md(players_not_responded)
        if player_text:
            to_return = f"*Waiting for {player_text} to respond to {self.name}.*"
            for player in players_not_responded:
                feedback = validation[player][1]
                if not feedback is None:
                    to_return += f"\n{self.sender.format_players_md([player])}: __{feedback}__"
            return to_return
        else:
            return f"*Not waiting for anyone to respond to {self.name}.*"
    def reset(self):
        self.responses = make_player_dict(self.players,None)
    async def _setup(self):
        pass
    async def _core(self):
        pass
    async def _unsetup(self):
        pass
    async def _update(self):
        await self.update_response_status()
        for func in self.funcs_to_call_on_update:
            await func()
    async def update_response_status(self):
        #to be called only one something has changed
        await self.sender(self.status_message)
    def recieved_responses(self) -> bool:
        #returns weather all responses in this input are no longer None
        return all(self._response_validator(player,self.responses[player])[0] for player in self.players)
    async def _run(self,await_task:asyncio.Task[Any]):
        await self._setup()
        await self._update()
        self._receive_inputs = True
        _core = asyncio.create_task(self._core())
        await asyncio.wait([await_task])
        _core.cancel()
        await self._unsetup()
    async def wait_until_received_all(self):
        #wait until all responses meet response validator
        while not self.recieved_responses():
            await asyncio.sleep(SLEEP_TIME)
        self._receive_inputs = False
    async def run(self) -> PlayerDictOptional[T]:
        #runs input until response validator is satisfied
        await_task = asyncio.create_task(self.wait_until_received_all())
        await self._run(await_task)
        return self.responses
class Player_Input_In_Response_To_Message[T](Player_Input[T]):
    def __init__(
            self, name:str, gi:Game_Interface, sender :Sender, 
            players:Optional[list[PlayerId]] = None, response_validator:ResponseValidator[T] = not_none,
            who_can_see:Optional[list[PlayerId]] = None,
            message:Optional[Message] = None, allow_edits:bool = True):
        Player_Input.__init__(self,name,gi,sender,players,response_validator,who_can_see)
        if message is None:
            self.message:Message = Message("Respond here.",players_who_can_see=players)
        else:
            self.message:Message = message
        self.allow_edits:bool = allow_edits
    def allow_interaction(self,interaction:Interaction) -> bool:
        if interaction.player_id is None:
            return False
        if not interaction.player_id in self.players:
            return False
        if not self.message.is_response(interaction):
            return False
        return (
            self.allow_edits or 
            self.responses[interaction.player_id] is None)
    async def _setup(self):
        if not self.message.is_sent():
            await self.sender(self.message)
        
class Player_Text_Input(Player_Input_In_Response_To_Message[str]):
    def __init__(
            self, name:str, gi:Game_Interface, sender :Sender, players:Optional[list[PlayerId]] = None, 
            response_validator:ResponseValidator[str] = not_none,
            who_can_see:Optional[list[PlayerId]] = None,
            message:Optional[Message] = None,
            allow_edits:bool = True):
        Player_Input_In_Response_To_Message.__init__(self,name,gi,sender,players,response_validator,who_can_see,message,allow_edits)
    async def _setup(self):
        await Player_Input_In_Response_To_Message._setup(self)
        @self.gi.on_action('send_message',self)
        async def on_message_action(interaction:Interaction):
            if self.allow_interaction(interaction):
                assert not interaction.player_id is None
                self.responses[interaction.player_id] = interaction.content
                await self._update()
        @self.gi.on_action('delete_message',self)
        async def on_delete_action(interaction:Interaction):
            if self.allow_interaction(interaction):
                assert not interaction.player_id is None
                self.responses[interaction.player_id] = None
                await self._update()
    async def _unsetup(self):
        self.gi.purge_actions(self)

class Player_Single_Choice_Input(Player_Input_In_Response_To_Message[int]):
    def __init__(
            self, name:str, gi:Game_Interface, sender :Sender, players:Optional[list[PlayerId]] = None, 
            response_validator:ResponseValidator[int] = not_none, 
            who_can_see:Optional[list[PlayerId]] = None,
            message:Optional[Message] = None,
            allow_edits:bool = True):
        Player_Input_In_Response_To_Message.__init__(self,name,gi,sender,players,response_validator,who_can_see,message,allow_edits)
    async def _setup(self):
        await Player_Input_In_Response_To_Message._setup(self)
        @self.gi.on_action('select_option',self)
        async def on_reaction_action(interaction:Interaction):
            if self.allow_interaction(interaction):
                assert not interaction.player_id is None
                self.responses[interaction.player_id] = interaction.choice_index
                await self._update()
        @self.gi.on_action('deselect_option',self)
        async def on_unreaction_action(interaction:Interaction):
            if self.allow_interaction(interaction):
                assert not interaction.player_id is None
                if self.responses[interaction.player_id] == interaction.choice_index:
                    self.responses[interaction.player_id] = None
                    await self._update()
    async def _unsetup(self):
        self.gi.purge_actions(self)
class Player_Multiple_Choice_Input(Player_Input_In_Response_To_Message[set[int]]):
    def __init__(
            self, name:str, gi:Game_Interface, sender :Sender, players:Optional[list[PlayerId]] = None, 
            response_validator:ResponseValidator[set[int]] = not_none,
            who_can_see:Optional[list[PlayerId]] = None, message:Optional[Message] = None):
        Player_Input_In_Response_To_Message.__init__(self,name,gi,sender,players,response_validator,who_can_see,message,True)
    async def _setup(self):
        await Player_Input_In_Response_To_Message._setup(self)
        @self.gi.on_action('select_option',self)
        async def on_reaction_action(interaction:Interaction):
            if self.allow_interaction(interaction) and not interaction.choice_index is None:
                assert not interaction.player_id is None
                if self.responses[interaction.player_id] is None:
                    self.responses[interaction.player_id] = set()
                proxy = self.responses[interaction.player_id]
                assert isinstance(proxy,set)
                proxy.add(interaction.choice_index)
                await self._update()
        @self.gi.on_action('deselect_option',self)
        async def on_unreaction_action(interaction:Interaction):
            if self.allow_interaction(interaction):
                assert not interaction.player_id is None
                if not self.responses[interaction.player_id] is None:
                    assert not interaction.choice_index is None
                    proxy = self.responses[interaction.player_id]
                    assert isinstance(proxy,set)
                    if interaction.choice_index in proxy:
                        proxy.remove(interaction.choice_index)
                        await self._update()
    async def _unsetup(self):
        self.gi.purge_actions(self)

async def run_inputs(
        inputs:list[Player_Input],completion_sets:Optional[list[set[Player_Input]]] = None,
        sender:Optional[Sender] = None,who_can_see:Optional[list[PlayerId]] = None):
    if completion_sets is None:
        completion_sets = [set(inputs)]
    def check_is_completion() -> bool:
        completed_inputs = set(input for input in inputs if input.recieved_responses())
        return any(completed_inputs == sub_set for sub_set in completion_sets)
    async def wait_until_completion():
        while not check_is_completion():
            await asyncio.sleep(SLEEP_TIME)
    if not sender is None:
        def feedback_text() -> str:
            feedback = ""
            for input in inputs:
                feedback += input.response_status() + '\n'
            return feedback
        feedback_message:Message = Alias_Message(
            Message(players_who_can_see=who_can_see),content_modifier=lambda content:feedback_text())
        await sender(feedback_message)
        async def on_update():
            await sender(feedback_message)
        for input in inputs:
            input.on_update(on_update)
        
    wait_task = asyncio.create_task(wait_until_completion())
    _runs = list(asyncio.create_task(input._run(wait_task)) for input in inputs)
    await asyncio.wait(_runs)
