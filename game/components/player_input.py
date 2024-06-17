import asyncio
from time import time
from typing import Any, Awaitable, Callable, Optional, override, Sequence
from uuid import uuid4

from config.config import config
from game import correct_str, get_logger, make_player_dict
from game.components.game_interface import Game_Interface
from game.components.interaction import Interaction
from game.components.message import Alias_Message
from game.components.response_validator import (
    ResponseValidator,
    Validation,
    default_text_validator,
    not_none,
)
from game.components.send.old_message import Old_Message
from game.components.send.sender import Sender
from utils.grammar import nice_time, ordinate
from utils.types import (
    GS,
    PlayerDict,
    PlayerDictOptional,
    PlayerId,
    PlayersIds,
    IDType
)

type Condition = dict[Player_Input,bool]
type OnUpdate = Callable[[],Awaitable]

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
            who_can_see:Optional[PlayersIds] = None, 
            timeout:Optional[int] = config['default_timeout'], warnings:list[int] = config['default_warnings']):
        self.id = str(uuid4())
        self.timeout = timeout
        self.warnings = warnings
        self.name = name
        self.gi = gi
        self.sender = sender
        self.who_can_see = None if who_can_see is None else tuple(who_can_see)
        self.players:PlayersIds = tuple(players)
        self.responses:PlayerDictOptional[T] = make_player_dict(self.players,None)
        self._receive_inputs = False
        self._response_validator:ResponseValidator[T] = response_validator
        self.status_message = Alias_Message(
            Old_Message(limit_players_who_can_see=self.who_can_see),lambda content: self.response_status())
        self.funcs_to_call_on_update:list[Callable[[],Awaitable]] = []
        self._last_response_status:str = ""
        self.timeout_time:int = 0
    @override
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"
    def on_update(self,func:OnUpdate) -> OnUpdate:
        """binds a callable to be run whenever the input changes"""
        if func not in self.funcs_to_call_on_update:
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
        players_with_feedback = list(player for player in self.players if validation[player][1] is not None)
        if player_text:
            to_return = f"*Waiting for {player_text} to respond to {self.name}.*"
        else:
            to_return = f"*Not waiting for anyone to respond to {self.name}.*"
        if not basic:
            for player in players_with_feedback:
                feedback = validation[player][1]
                if feedback is not None:
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
        status_message_content = self.status_message.content
        if status_message_content != self._last_response_status:
            self._last_response_status = correct_str(status_message_content)
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
            if self.timeout is not None:
                timeout_text = f"\nYou have {nice_time(self.timeout_time-int(time()))} to respond before timeout."
            await self.sender(Old_Message(
                limit_players_who_can_see=self.who_can_see,
                text=f"We are still waiting on {self.sender.format_players_md(players_not_responded)} to respond to {self.name}.\n" +
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
            await self.sender(Old_Message(
                limit_players_who_can_see=self.who_can_see,
                text=f"The opportunity to respond to {self.name} has timed out."))
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
    @override
    def __hash__(self) -> int:#it is very bad that I need this
        return hash((self.name,self.players,self.who_can_see,self.id))
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
            message:Optional[Old_Message|str] = None, allow_edits:bool = True):
        Player_Input.__init__(self,name,gi,sender,players,response_validator,who_can_see,timeout,warnings)
        self.message:Old_Message
        _message:Old_Message
        if message is None:
            _message = Old_Message("Respond here.",limit_players_who_can_see=players)
        elif isinstance(message,str):
            _message = Old_Message(message,limit_players_who_can_see=players)
        else:
            _message:Old_Message = message
        self.bind_message(_message)
        self.allow_edits:bool = allow_edits
    def bind_message(self,message:Old_Message) -> Old_Message:
        self.message = Alias_Message(message,lambda content: self.add_response_status(content))
        return self.message
    @override
    def response_status(self, basic: bool = False) -> str:
        return super().response_status(basic) + f" *(Edits are {'not ' if not self.allow_edits else ''}allowed.)*"
    @override
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
        if interaction.player_id not in self.players:
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
    @override
    async def _setup(self):
        if not self.message.is_sent():
            await self.sender(self.message)
    @override
    async def _unsetup(self):
        await super()._unsetup()
        self.gi.purge_actions(self)
class Player_Text_Input(Player_Input_In_Response_To_Message[str]):
    """
    player input class for collecting text interactions to a message
    """
    def __init__(
            self, name:str, gi:Game_Interface, sender :Sender, players:PlayersIds, 
            response_validator:ResponseValidator[str] = default_text_validator,
            who_can_see:Optional[list[PlayerId]] = None, 
            timeout:Optional[int] = config['default_timeout'], warnings:list[int] = config['default_warnings'],
            message:Optional[Old_Message|str] = None,
            allow_edits:bool = True):
        Player_Input_In_Response_To_Message.__init__(self,name,gi,sender,players,response_validator,who_can_see,timeout,warnings,message,allow_edits)
    @override
    async def _setup(self):
        await Player_Input_In_Response_To_Message._setup(self)
        @self.gi.on_action('send_message',self)
        async def on_message_action(interaction:Interaction):
            if self.allow_interaction(interaction):
                assert interaction.player_id is not None
                self.responses[interaction.player_id] = interaction.content
                await self._update()
        @self.gi.on_action('delete_message',self)
        async def on_delete_action(interaction:Interaction):
            if self.allow_interaction(interaction):
                assert interaction.player_id is not None
                self.responses[interaction.player_id] = None
                await self._update()
class Player_Multi_Text_Input(Player_Input_In_Response_To_Message[set[str]]):
    def __init__(
            self, 
            name: str, 
            gi: Game_Interface, 
            sender: Sender, 
            players: PlayersIds, 
            response_validator: Callable[[PlayerId, set[str] | None], tuple[bool, str | None]] = not_none, 
            who_can_see: list[PlayerId] | None = None, 
            timeout: int | None = config['default_timeout'], 
            warnings: list[int] = config['default_warnings'], 
            message: Old_Message | str | None = None, 
            allow_edits: bool = True):
        Player_Input_In_Response_To_Message.__init__(self,name, gi, sender, players, response_validator, who_can_see, timeout, warnings, message, allow_edits)
    @override
    async def _setup(self):
        await Player_Input_In_Response_To_Message._setup(self)
        @self.gi.on_action('send_message',self)
        async def on_message_action(interaction:Interaction):
            if self.allow_interaction(interaction) and interaction.content is not None:
                assert interaction.player_id is not None
                response = self.responses[interaction.player_id]
                if response is None:
                    response = set()
                    self.responses[interaction.player_id] = response
                response.add(interaction.content)
                await self._update()
        @self.gi.on_action('delete_message',self)
        async def on_delete_action(interaction:Interaction):
            if self.allow_interaction(interaction) and interaction.content is not None:
                assert interaction.player_id is not None
                response = self.responses[interaction.player_id]
                if response is None:
                    return
                response.remove(interaction.content)
                await self._update()
class Player_Single_Selection_Input(Player_Input_In_Response_To_Message[int]):
    """
    player input class for collecting single choice selection interactions to a message
    """
    def __init__(
            self, name:str, gi:Game_Interface, sender :Sender, players:PlayersIds, 
            response_validator:ResponseValidator[int] = not_none, 
            who_can_see:Optional[list[PlayerId]] = None, 
            timeout:Optional[int] = config['default_timeout'], warnings:list[int] = config['default_warnings'],
            message:Optional[Old_Message|str] = None,
            allow_edits:bool = True):
        Player_Input_In_Response_To_Message.__init__(self,name,gi,sender,players,response_validator,who_can_see,timeout,warnings,message,allow_edits)
    @override
    async def _setup(self):
        await Player_Input_In_Response_To_Message._setup(self)
        @self.gi.on_action('select_option',self)
        async def on_reaction_action(interaction:Interaction):
            if self.allow_interaction(interaction):
                assert interaction.player_id is not None
                self.responses[interaction.player_id] = interaction.choice_index
                await self._update()
        @self.gi.on_action('deselect_option',self)
        async def on_unreaction_action(interaction:Interaction):
            if self.allow_interaction(interaction):
                assert interaction.player_id is not None
                if self.responses[interaction.player_id] == interaction.choice_index:
                    self.responses[interaction.player_id] = None
                    await self._update()
class Player_Multiple_Selection_Input(Player_Input_In_Response_To_Message[set[int]]):
    """
    player input class for collecting multiple choice selection interactions to a message
    """
    def __init__(
            self, name:str, gi:Game_Interface, sender :Sender, players:PlayersIds, 
            response_validator:ResponseValidator[set[int]] = not_none,
            who_can_see:Optional[list[PlayerId]] = None, 
            timeout:Optional[int] = config['default_timeout'], warnings:list[int] = config['default_warnings'], message:Optional[Old_Message|str] = None):
        Player_Input_In_Response_To_Message.__init__(self,name,gi,sender,players,response_validator,who_can_see,timeout,warnings,message,True)
    @override
    async def _setup(self):
        await Player_Input_In_Response_To_Message._setup(self)
        @self.gi.on_action('select_option',self)
        async def on_reaction_action(interaction:Interaction):
            if self.allow_interaction(interaction) and interaction.choice_index is not None:
                assert interaction.player_id is not None
                if self.responses[interaction.player_id] is None:
                    self.responses[interaction.player_id] = set()
                proxy = self.responses[interaction.player_id]
                assert isinstance(proxy,set)
                proxy.add(interaction.choice_index)
                await self._update()
        @self.gi.on_action('deselect_option',self)
        async def on_unreaction_action(interaction:Interaction):
            if self.allow_interaction(interaction):
                assert interaction.player_id is not None
                if self.responses[interaction.player_id] is not None:
                    assert interaction.choice_index is not None
                    proxy = self.responses[interaction.player_id]
                    assert isinstance(proxy,set)
                    if interaction.choice_index in proxy:
                        proxy.remove(interaction.choice_index)
                        await self._update()
def multi_bind_message(message:Old_Message,*player_inputs:Player_Input_In_Response_To_Message):
    """
    binds a single message to multiple inputs correctly
    
    message: the message to be bound to all of the inputs
    
    player_inputs: all the player inputs the message should be bound to
    """
    _message:Old_Message = message
    for player_input in player_inputs:
        _message = player_input.bind_message(_message)
    for player_input in player_inputs:
        player_input.message = _message
async def run_inputs(
        inputs:Sequence[Player_Input[Any]],
        completion_sets:Optional[list[set[Player_Input[Any]]]] = None,
        sender:Optional[Sender] = None,
        who_can_see:Optional[PlayersIds] = None,
        codependent:bool = False, 
        basic_feedback:bool = False, 
        id:Optional[IDType] = None, 
        sync_call:Callable[[IDType,bool],bool]|None = None):
    """
    runs inputs simultaniously until completion criteria are met

    inputs: a list of fully configured inputs

    completions_sets: a list of sets of inputs from inputs for which if all of the inputs in a set mark themselves complete, the code will exit; if set to None, will default to a set of all inputs

    sender: the sender to use for displaying feedback; if set to None the function will not display its own feedback

    who_can_see: the list of people who are allowed to see the feedback, set as the feedback message's who_can_see variable

    codependant: sets where a change in one input should update all the other inputs

    basic_feedback: sets whether the feedback, if it exists, should be limited to only whether an input is complete or not; True for limited, False for unlimited
    """
    run_input_id:IDType
    if id is None:
        run_input_id = str(uuid4())#type:ignore
    else:
        run_input_id = id
    logger.info(f"RUN_INPUTS({run_input_id}): starting with inputs = f{inputs}")
    if completion_sets is None:
        completion_sets = [set(inputs)]
    logger.info(f"RUN_INPUTS({run_input_id}): waiting on completion_sets = {completion_sets}")
    def check_is_completion() -> bool:
        completed_inputs = set(input for input in inputs if input.has_recieved_all_responses())
        completed:bool = any(completed_inputs == sub_set for sub_set in completion_sets)
        if sync_call is not None:
            completed = sync_call(run_input_id,completed)
        logger.debug(f"RUN_INPUTS({run_input_id}): completed = {completed} with completed_inputs = {completed_inputs}")
        return completed
    async def wait_until_completion():
        while not check_is_completion():
            await asyncio.sleep(SLEEP_TIME)
    if sender is not None:
        logger.info(f"RUN_INPUTS({run_input_id}): setting up feedback")
        def feedback_text() -> str:
            feedback_list = []
            for input in (input for input in inputs if not input.has_recieved_all_responses()):
                feedback_list.append("Monitoring: " + input.response_status(basic_feedback))
            if len(feedback_list) == 0:
                return "*All inputs are satisfied.*"
            else:
                return "\n".join(feedback_list)
        feedback_message:Old_Message = Alias_Message(
            Old_Message(limit_players_who_can_see=who_can_see),content_modifier=lambda content:feedback_text())
        await sender(feedback_message)
        async def on_update():
            await sender(feedback_message)
        for input in inputs:
            input.on_update(on_update)
    else:
        logger.info(f"RUN_INPUTS({run_input_id}): supressing feedback")
    if codependent:
        logger.info(f"RUN_INPUTS({run_input_id}): setting up codependencies")
        for input1 in inputs:
            for input2 in inputs:
                if input1 != input2:
                    input1.on_update(input2.update_response_status)#didn't work!!!!!!!
    logger.info(f"RUN_INPUTS({run_input_id}): creating the wait task")
    wait_task = asyncio.create_task(wait_until_completion())
    logger.info(f"RUN_INPUTS({run_input_id}): creating the input tasks")
    _runs = list(asyncio.create_task(input._run(wait_task)) for input in inputs)
    all_tasks = [wait_task]+_runs
    #determine cumulitive timout
    """timeout_mins = list(min(
        (pinput.timeout if not pinput.timeout is None else float('inf'))
        for pinput in group) for group in completion_sets)"""
    logger.info(f"RUN_INPUTS({run_input_id}): waiting for all tasks to be done")
    await asyncio.wait(all_tasks)
    logger.info(f"all criteria are met with inputs = {inputs}")
    await asyncio.sleep(5)#give tasks some time to finish
    for task in all_tasks:
        if not task.done():
            task.cancel()
    #make sure feedback is correct when we exit
    if sender is not None:
        await sender(feedback_message)
    logger.info(f"RUN_INPUTS({run_input_id}): waiting is over")
