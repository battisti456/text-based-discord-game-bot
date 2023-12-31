from game import PlayerId,PlayerDict,PlayerDictOptional, make_player_dict, correct_str
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
    """
    base player input class
    
    meant only to be overwritten
    """
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
        self._last_response_status:str = ""
    def on_update(self,func:Callable[[],Awaitable]) -> Callable[[],Awaitable]:
        """binds a callable to be run whenever the input changes"""
        if not func in self.funcs_to_call_on_update:
            self.funcs_to_call_on_update.append(func)
        return func
    def response_status(self, basic:bool = False) -> str:
        """
        generates a string representing the current state of the input
        
        basic : controls weather to include validation feedback in the returned string,
        True excludes, False includes
        """
        #returns text describing which players have not responded to this input
        validation:PlayerDict[Validation] = {player:self._response_validator(player,self.responses[player]) for player in self.players}
        players_not_responded = list(player for player in self.players if not validation[player][0])
        player_text = self.sender.format_players_md(players_not_responded)
        players_with_feedback = list(player for player in self.players if not validation[player][1] is None)
        if player_text:
            to_return = f"*Waiting for {player_text} to respond to {self.name}.*"
        else:
            to_return = f"*Not waiting for anyone to respond to {self.name}.*"
        if not basic:
            for player in players_with_feedback:
                feedback = validation[player][1]
                if not feedback is None:
                    to_return += f"\n{self.sender.format_players_md([player])}: __{feedback}__"
        return to_return
    def reset(self):
        """
        prepares the input to be run again by clearing responses
        """
        self.responses = make_player_dict(self.players,None)
    async def _setup(self):
        """run once and awaited in _run at the beggining"""
        pass
    async def _core(self):
        """
        run once and not awaited in _run while waiting for await_task to finish
        
        will be cancelled if it takes too long
        """
        pass
    async def _unsetup(self):
        """run once and awaited in _run at the end"""
        pass
    async def _update(self):
        """called during running only when an input is changed"""
        await self.update_response_status()
        for func in self.funcs_to_call_on_update:
            await func()
    async def update_response_status(self):
        """updates status_message, if it is different"""
        if self.status_message.content != self._last_response_status:
            self._last_response_status = correct_str(self.status_message.content)
            await self.sender(self.status_message)
    def has_recieved_all_responses(self) -> bool:
        """returns whether all responses meet the validator's requirements"""
        return all(self._response_validator(player,self.responses[player])[0] for player in self.players)
    async def _run(self,await_task:asyncio.Task[Any]):
        """
        awaits's _setup, then calls _core while it awaits await_task, then calls _unsetup
        
        await_task : an asyncio.Task to call ayncio.wait on during running
        """
        await self._setup()
        await self._update()
        self._receive_inputs = True
        _core = asyncio.create_task(self._core())
        await asyncio.wait([await_task])
        _core.cancel()
        await self._unsetup()
    async def wait_until_received_all(self):
        """
        waits until has_received_all_responses, check every SLEEP_TIME seconds
        """
        while not self.has_recieved_all_responses():
            await asyncio.sleep(SLEEP_TIME)
        self._receive_inputs = False
    async def run(self) -> PlayerDictOptional[T]:
        """
        collects and return player responses to the input

        calls _run with wait_until_received_all as the wait task
        """
        await_task = asyncio.create_task(self.wait_until_received_all())
        await self._run(await_task)
        return self.responses
class Player_Input_In_Response_To_Message[T](Player_Input[T]):
    """
    base player input class for reacting to interactions sent by the game_interface in response to a message

    meant to be overwritten
    """
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
        self.message = Alias_Message(self.message,lambda content: self.add_response_status(content))
        self.allow_edits:bool = allow_edits
    async def update_response_status(self):
        await self.sender(self.message)
    def add_response_status(self,content:str|None):
        if content is None:
            return self.response_status()
        else:
            return content +'\n' + self.response_status()
    def allow_interaction(self,interaction:Interaction) -> bool:
        """
        returns wether a particular interaction is auctually meant for this player_input's message
        
        it does not check if the interaction is valid according to the validifier
        """
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
    """
    player input class for collecting text interactions to a message
    """
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
    """
    player input class for collecting single choice selection interactions to a message
    """
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
    """
    player input class for collecting multiple choice selection interactions to a message
    """
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
        sender:Optional[Sender] = None,who_can_see:Optional[list[PlayerId]] = None,
        codependant:bool = False, basic_feedback:bool = False):
    """
    runs inputs simultaniously until completion criteria are met

    inputs: a list of fully configured inputs

    completions_sets: a list of sets of inputs from inputs for which if all of the inputs in a set mark themselves complete, the code will exit; if set to None, will default to a set of all inputs

    sender: the sender to use for displaying feedback; if set to None the function will not display its own feedback

    who_can_see: the list of people who are allowed to see the feedback, set as the feedback message's who_can_see variable

    codependant: sets wher a change in one input should update all the other inputs

    basic_feedback: sets whether the feedback, if it exists, should be limited to only whether an input is complete or not; True for limited, False for unlimited
    """
    if completion_sets is None:
        completion_sets = [set(inputs)]
    def check_is_completion() -> bool:
        completed_inputs = set(input for input in inputs if input.has_recieved_all_responses())
        return any(completed_inputs == sub_set for sub_set in completion_sets)
    async def wait_until_completion():
        while not check_is_completion():
            await asyncio.sleep(SLEEP_TIME)
    if not sender is None:
        def feedback_text() -> str:
            feedback_list = []
            for input in inputs:
                feedback_list.append("Monitoring: " + input.response_status(basic_feedback))
            return "\n".join(feedback_list)
        feedback_message:Message = Alias_Message(
            Message(players_who_can_see=who_can_see),content_modifier=lambda content:feedback_text())
        await sender(feedback_message)
        async def on_update():
            await sender(feedback_message)
        for input in inputs:
            input.on_update(on_update)
    if codependant:
        for input1 in inputs:
            for input2 in inputs:
                if input1 != input2:
                    input1.on_update(input2.update_response_status)#didn't work!!!!!!!
    wait_task = asyncio.create_task(wait_until_completion())
    _runs = list(asyncio.create_task(input._run(wait_task)) for input in inputs)
    await asyncio.wait([wait_task]+_runs)
