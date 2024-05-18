from config.config import config

from game.utils.types import PlayerDict, PlayerDictOptional, PlayersIds

from game import make_player_dict, correct_str, get_logger
from game.components.sender import Sender
from game.components.message import Message, Alias_Message
from game.components.game_interface import Game_Interface
from game.components.interaction import Interaction
from game.components.response_validator import ResponseValidator, Validation, not_none, default_text_validator
from game.utils.grammer import nice_time, ordinate
from game.utils.types import Grouping, GS, PlayerId

from typing import Optional, Any, Callable, Awaitable

import asyncio
from time import time
type Condition = dict[Player_Input,bool]

logger = get_logger(__name__)
SLEEP_TIME = 10

class Player_Input[T](GS):
    """
    base player input class
    
    meant only to be overwritten
    """
    def __init__(
            self,name:str, gi:Game_Interface,sender:Sender,players:PlayersIds,
            response_validator:ResponseValidator[T] = not_none, 
            who_can_see:Optional[Grouping[PlayerId]] = None, 
            timeout:Optional[int] = config['default_timeout'], warnings:list[int] = config['default_warnings']):
        self.timeout = timeout
        self.warnings = warnings
        self.name = name
        self.gi = gi
        self.sender = sender
        self.who_can_see = who_can_see
        self.players:PlayersIds = players
        self.responses:PlayerDictOptional[T] = make_player_dict(self.players,None)
        self._receive_inputs = False
        self._response_validator:ResponseValidator[T] = response_validator
        self.status_message = Alias_Message(
            Message(players_who_can_see=self.who_can_see),lambda content: self.response_status())
        self.funcs_to_call_on_update:list[Callable[[],Awaitable]] = []
        self._last_response_status:str = ""
        self.timeout_time:int = 0
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"
    def on_update(self,func:Callable[[],Awaitable]) -> Callable[[],Awaitable]:
        """binds a callable to be run whenever the input changes"""
        if not func in self.funcs_to_call_on_update:
            logger.info(f"bound new on_update to {self}")
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
        logger.warning(f"resetting {self}")
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
        logger.info(f"{self} has updated, calling {len(self.funcs_to_call_on_update)} on_updates")
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
        to_return:bool = all(self._response_validator(player,self.responses[player])[0] for player in self.players)
        logger.debug(f"{self} has evaluated that is has" + ("n't" if not to_return else "") + " received all responses")
        return all(self._response_validator(player,self.responses[player])[0] for player in self.players)
    async def _handle_warnings(self):
        if self.timeout is None:
            return
        for i in range(len(self.warnings)):
            await asyncio.sleep(self.timeout_time-self.timeout+self.warnings[i]-int(time()))
            players_not_responded = list(player for player in self.players if not self._response_validator(player,self.responses[player])[0])
            if len(players_not_responded) == 0:
                continue
            warning_text:str
            if i + 1 == len(self.warnings):
                warning_text = "This is your final warning."
            else:
                warning_text = f"You have {len(self.warnings)-1-i} warning(s) remaining."
            timeout_text:str = ""
            if not self.timeout is None:
                timeout_text = f"\nYou have {nice_time(self.timeout_time-int(time()))} to respond before timeout."
            await self.sender(Message(
                players_who_can_see=self.who_can_see,
                content=f"We are still waiting on {self.sender.format_players_md(players_not_responded)} to respond to {self.name}.\n" +
                f"This is your {ordinate(i+1)} warning at {nice_time(self.warnings[i])} of failure to respond.\n" + 
                warning_text + timeout_text
                ))
    async def _run(self,await_task:asyncio.Task[Any]):
        """
        awaits's _setup, then calls _core while it awaits await_task, then calls _unsetup
        
        await_task : an asyncio.Task to call ayncio.wait on during running
        """
        await self._setup()
        await self._update()
        self._receive_inputs = True
        _core = asyncio.create_task(self._core())
        _handle_warnings = asyncio.create_task(self._handle_warnings())
        if isinstance(self.timeout,int):
            self.timeout_time = int(time()) + self.timeout
        try:
            await asyncio.wait_for(await_task,timeout=self.timeout)
        except asyncio.TimeoutError:
            await self.sender(Message(
                players_who_can_see=self.who_can_see,
                content=f"The opportunity to respond to {self.name} has timed out."))
        _core.cancel()
        _handle_warnings.cancel()
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
        logger.info(f"{self} is starting to run independantly")
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
            players:PlayersIds, response_validator:ResponseValidator[T] = not_none,
            who_can_see:Optional[list[PlayerId]] = None, 
            timeout:Optional[int] = config['default_timeout'], warnings:list[int] = config['default_warnings'],
            message:Optional[Message|str] = None, allow_edits:bool = True):
        Player_Input.__init__(self,name,gi,sender,players,response_validator,who_can_see,timeout,warnings)
        self.message:Message
        _message:Message
        if message is None:
            _message = Message("Respond here.",players_who_can_see=players)
        elif isinstance(message,str):
            _message = Message(message,players_who_can_see=players)
        else:
            _message:Message = message
        self.bind_message(_message)
        self.allow_edits:bool = allow_edits
    def bind_message(self,message:Message) -> Message:
        self.message = Alias_Message(message,lambda content: self.add_response_status(content))
        return self.message
    def response_status(self, basic: bool = False) -> str:
        return super().response_status(basic) + f" *(Edits are {'not ' if not self.allow_edits else ''}allowed.)*"
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
            logger.info(f"{interaction} ignored by {self} because it had no player_id")
            return False
        if not interaction.player_id in self.players:
            logger.info(f"{interaction} ignored by {self} because its player_id was not listed for the input")
            return False
        if not self.message.is_response(interaction):
            logger.info(f"{interaction} ignored by {self} because it was not a response to the message")
            return False
        val = self.allow_edits or not self._response_validator(interaction.player_id,self.responses[interaction.player_id])[0]
        if not val:
            logger.info(f"{interaction} ignored by {self} because edits are not allowed and they already have a valid response of '{self.responses[interaction.player_id]}'")
            return False
        return True
    async def _setup(self):
        if not self.message.is_sent():
            await self.sender(self.message)
        
class Player_Text_Input(Player_Input_In_Response_To_Message[str]):
    """
    player input class for collecting text interactions to a message
    """
    def __init__(
            self, name:str, gi:Game_Interface, sender :Sender, players:PlayersIds, 
            response_validator:ResponseValidator[str] = default_text_validator,
            who_can_see:Optional[list[PlayerId]] = None, 
            timeout:Optional[int] = config['default_timeout'], warnings:list[int] = config['default_warnings'],
            message:Optional[Message|str] = None,
            allow_edits:bool = True):
        Player_Input_In_Response_To_Message.__init__(self,name,gi,sender,players,response_validator,who_can_see,timeout,warnings,message,allow_edits)
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

class Player_Single_Selection_Input(Player_Input_In_Response_To_Message[int]):
    """
    player input class for collecting single choice selection interactions to a message
    """
    def __init__(
            self, name:str, gi:Game_Interface, sender :Sender, players:PlayersIds, 
            response_validator:ResponseValidator[int] = not_none, 
            who_can_see:Optional[list[PlayerId]] = None, 
            timeout:Optional[int] = config['default_timeout'], warnings:list[int] = config['default_warnings'],
            message:Optional[Message|str] = None,
            allow_edits:bool = True):
        Player_Input_In_Response_To_Message.__init__(self,name,gi,sender,players,response_validator,who_can_see,timeout,warnings,message,allow_edits)
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
class Player_Multiple_Selection_Input(Player_Input_In_Response_To_Message[set[int]]):
    """
    player input class for collecting multiple choice selection interactions to a message
    """
    def __init__(
            self, name:str, gi:Game_Interface, sender :Sender, players:PlayersIds, 
            response_validator:ResponseValidator[set[int]] = not_none,
            who_can_see:Optional[list[PlayerId]] = None, 
            timeout:Optional[int] = config['default_timeout'], warnings:list[int] = config['default_warnings'], message:Optional[Message|str] = None):
        Player_Input_In_Response_To_Message.__init__(self,name,gi,sender,players,response_validator,who_can_see,timeout,warnings,message,True)
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
def multi_bind_message(message:Message,*player_inputs:Player_Input_In_Response_To_Message):
    """
    binds a single message to multiple inputs correctly
    
    message: the message to be bound to all of the inputs
    
    player_inputs: all the player inputs the message should be bound to
    """
    _message:Message = message
    for player_input in player_inputs:
        _message = player_input.bind_message(_message)
    for player_input in player_inputs:
        player_input.message = _message
async def run_inputs(
        inputs:Grouping[Player_Input[Any]],completion_sets:Optional[list[set[Player_Input[Any]]]] = None,
        sender:Optional[Sender] = None,who_can_see:Optional[PlayersIds] = None,
        codependant:bool = False, basic_feedback:bool = False):
    """
    runs inputs simultaniously until completion criteria are met

    inputs: a list of fully configured inputs

    completions_sets: a list of sets of inputs from inputs for which if all of the inputs in a set mark themselves complete, the code will exit; if set to None, will default to a set of all inputs

    sender: the sender to use for displaying feedback; if set to None the function will not display its own feedback

    who_can_see: the list of people who are allowed to see the feedback, set as the feedback message's who_can_see variable

    codependant: sets where a change in one input should update all the other inputs

    basic_feedback: sets whether the feedback, if it exists, should be limited to only whether an input is complete or not; True for limited, False for unlimited
    """
    logger.info(f"run_inputs starting with inputs = f{inputs}")
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
            for input in (input for input in inputs if not input.has_recieved_all_responses()):
                feedback_list.append("Monitoring: " + input.response_status(basic_feedback))
            return "\n".join(feedback_list)
        feedback_message:Message = Alias_Message(
            Message(players_who_can_see=who_can_see),content_modifier=lambda content:feedback_text())
        await sender(feedback_message)
        async def on_update():
            await sender(feedback_message)
        for input in inputs:
            input.on_update(on_update)
    else:
        logger.info("run_inputs supressing feedback")
    if codependant:
        for input1 in inputs:
            for input2 in inputs:
                if input1 != input2:
                    input1.on_update(input2.update_response_status)#didn't work!!!!!!!
    wait_task = asyncio.create_task(wait_until_completion())
    _runs = list(asyncio.create_task(input._run(wait_task)) for input in inputs)
    all_tasks = [wait_task]+_runs
    #determine cumulitive timout
    """timeout_mins = list(min(
        (pinput.timeout if not pinput.timeout is None else float('inf'))
        for pinput in group) for group in completion_sets)"""
    await asyncio.wait(all_tasks)
    """for task in all_tasks:
        task.cancel()"""
