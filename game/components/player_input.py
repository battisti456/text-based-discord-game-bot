import asyncio
from time import time
from typing import Any, Awaitable, Callable, Optional, Sequence, override
from uuid import uuid4

from config.config import config
from game import correct_str, get_logger, make_player_dict
from game.components.game_interface import Game_Interface
from game.components.response_validator import (
    ResponseValidator,
    Validation,
    default_text_validator,
    not_none,
)
from game.components.send import Address, Sender
from game.components.send.interaction import Interaction, Select_Options, Send_Text
from game.components.send.old_message import Old_Message
from game.components.send.sendable.sendables import Text_Only
from utils.grammar import nice_time, ordinate
from utils.types import GS, IDType, PlayerDict, PlayerDictOptional, PlayerId, PlayersIds

type Condition = dict[Player_Input,bool]
type OnUpdate = Callable[[],Awaitable[None]]

logger = get_logger(__name__)
SLEEP_TIME = 10

class Player_Input[T](GS):
    """
    base player input class
    
    meant only to be overwritten
    """
    def __init__(
            self,
            name:str, 
            gi:Game_Interface,
            sender:Sender,
            players:PlayersIds,
            *,
            response_validator:ResponseValidator[T] = not_none, 
            who_can_see:Optional[PlayersIds] = None, 
            timeout:Optional[int] = config['default_timeout'], 
            warnings:list[int] = config['default_warnings'],
            status_address:Address|None = None):
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
        self.status_address:Address|None = status_address
        self.funcs_to_call_on_update:list[Callable[[],Awaitable]] = []
        self._last_response_status:Text_Only|None = None
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
        """run once and awaited in _run at the beginning"""
        await self.update_response_status()
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
        if self.status_address is None:
            self.status_address = await self.sender.generate_address()
        sendable = Text_Only(text=self.response_status())
        if sendable != self._last_response_status:
            await self.sender(sendable,self.status_address)
            self._last_response_status = sendable
    def has_received_all_responses(self) -> bool:
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
        while not self.has_received_all_responses():
            await asyncio.sleep(SLEEP_TIME)
        self._receive_inputs = False
    async def run(self) -> PlayerDictOptional[T]:
        """
        collects and return player responses to the input

        calls _run with wait_until_received_all as the wait task
        """
        logger.info(f"{self} is starting to run independently")
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
            self, 
            name:str, 
            gi:Game_Interface, 
            sender :Sender, 
            players:PlayersIds,
            *, 
            response_validator:ResponseValidator[T] = not_none,
            who_can_see:Optional[list[PlayerId]] = None, 
            timeout:Optional[int] = config['default_timeout'], 
            warnings:list[int] = config['default_warnings'],
            status_address:Address|None = None,
            question_address:Address|None = None,
            allow_edits:bool = True):
        Player_Input.__init__(
            self,name,gi,sender,players,
            response_validator=response_validator,
            who_can_see=who_can_see,
            timeout=timeout,
            warnings=warnings,
            status_address=status_address)
        self.question_address:None|Address = question_address
        self.allow_edits:bool = allow_edits
    @override
    def response_status(self, basic: bool = False) -> str:
        return super().response_status(basic)
    @override
    async def update_response_status(self):
        if self.question_address is None:
            self.question_address = await self.sender(Text_Only(text = "Please respond here."))
        if self.status_address is None:
            self.status_address = await self.sender.generate_address(self.question_address)
        await Player_Input.update_response_status(self)
    def add_response_status(self,content:str|None):
        if content is None:
            return self.response_status()
        else:
            return content +'\n' + self.response_status()
    def allow_interaction(self,interaction:Interaction) -> bool:
        """
        returns wether a particular interaction is actually meant for this player_input's message
        
        it does not check if the interaction is valid according to the validifier
        """
        if interaction.by_player not in self.players:
            logger.info(f"{interaction} ignored by {self} because its player_id was not listed for the input")
            return False
        if not interaction.at_address == self.question_address:
            logger.info(f"{interaction} ignored by {self} because it was not a response to the message")
            return False
        val = self.allow_edits or not self._response_validator(interaction.by_player,self.responses[interaction.by_player])[0]
        if not val:
            logger.info(f"{interaction} ignored by {self} because edits are not allowed and they already have a valid response of '{self.responses[interaction.by_player]}'")
            return False
        return True
    @override
    async def _unsetup(self):
        await super()._unsetup()
        self.gi.purge_actions(self)
class Player_Text_Input(Player_Input_In_Response_To_Message[str]):
    """
    player input class for collecting text interactions to a message
    """
    def __init__(
            self, 
            name:str, 
            gi:Game_Interface, 
            sender :Sender, 
            players:PlayersIds,
            *,
            response_validator:ResponseValidator[str] = default_text_validator,
            who_can_see:Optional[list[PlayerId]] = None, 
            timeout:Optional[int] = config['default_timeout'], 
            warnings:list[int] = config['default_warnings'],
            status_address:Address|None = None,
            question_address:Address|None = None,
            allow_edits:bool = True):
        Player_Input_In_Response_To_Message.__init__(
            self,name,gi,sender,players,
            response_validator=response_validator,
            who_can_see=who_can_see,
            timeout=timeout,
            warnings=warnings,
            status_address=status_address,
            question_address=question_address,
            allow_edits=allow_edits)
    @override
    async def _setup(self):
        await Player_Input_In_Response_To_Message._setup(self)
        @self.gi.watch(
                owner = self,
                filter=lambda interaction: isinstance(interaction.content,Send_Text))
        async def on_message_action(interaction:Interaction):
            if self.allow_interaction(interaction):
                assert isinstance(interaction.content,Send_Text)
                self.responses[interaction.by_player] = interaction.content.text
                await self._update()

class Player_Single_Selection_Input(Player_Input_In_Response_To_Message[int]):
    """
    player input class for collecting single choice selection interactions to a message
    """
    def __init__(
            self,
            name:str,
            gi:Game_Interface,
            sender :Sender,
            players:PlayersIds,
            *,
            response_validator:ResponseValidator[int] = not_none, 
            who_can_see:Optional[list[PlayerId]] = None, 
            timeout:Optional[int] = config['default_timeout'], 
            warnings:list[int] = config['default_warnings'],
            status_address:Address|None = None,
            question_address:Address|None = None,
            allow_edits:bool = True):
        Player_Input_In_Response_To_Message.__init__(
            self,name,gi,sender,players,
            response_validator=response_validator,
            who_can_see=who_can_see,
            timeout=timeout,
            warnings=warnings,
            status_address=status_address,
            question_address=question_address,
            allow_edits=allow_edits)
    @override
    async def _setup(self):
        await Player_Input_In_Response_To_Message._setup(self)
        @self.gi.watch(
                owner = self,
                filter=lambda interaction:isinstance(interaction.content,Select_Options))
        async def on_reaction_action(interaction:Interaction):
            if self.allow_interaction(interaction):
                assert isinstance(interaction.content,Select_Options)
                if len(interaction.content.indices) > 1:
                    logger.warning(f"received extra inputs in {self} from {interaction}")
                if len(interaction.content.indices) < 1:
                    logger.error(f"received an interaction with zero selected on {self} from {interaction}")
                    return
                self.responses[interaction.by_player] = interaction.content.indices[0]
                await self._update()
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
    runs inputs simultaneously until completion criteria are met

    inputs: a list of fully configured inputs

    completions_sets: a list of sets of inputs from inputs for which if all of the inputs in a set mark themselves complete, the code will exit; if set to None, will default to a set of all inputs

    sender: the sender to use for displaying feedback; if set to None the function will not display its own feedback

    who_can_see: the list of people who are allowed to see the feedback, set as the feedback message's who_can_see variable

    codependent: sets where a change in one input should update all the other inputs

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
        completed_inputs = set(input for input in inputs if input.has_received_all_responses())
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
            for input in (input for input in inputs if not input.has_received_all_responses()):
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
        logger.info(f"RUN_INPUTS({run_input_id}): suppressing feedback")
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
    #determine cumulative timeout
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
