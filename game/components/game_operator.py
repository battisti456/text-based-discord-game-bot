import asyncio
import inspect
import shlex
from ast import literal_eval
from typing import (
    Any,
    Callable,
    Iterable,
    Literal,
    Optional,
    Sequence,
    get_args,
    get_origin,
    get_type_hints,
)

from docopt import DocoptExit, docopt
from typing_extensions import TypeVar

from config.config import config
from config.config_tools import ConfigAction, ConfigError
from config.config_tools import edit as config_edit
from utils.logging import get_logger
from game.components.game_interface import Game_Interface
from game.components.interface_operator import Interface_Operator
from game.components.send import Interaction
from game.components.send.interaction import Send_Text
from game.components.send.sendable.sendables import Text_Only
from game.game import Game
from game.games import random_game, search_games, valid_games
from utils.common import get_first
from utils.grammar import wordify_iterable

logger = get_logger(__name__)

CP = config['command_prefix']
COMMAND_DOCSTRING= f"""
Usage:
    {CP} (h | help) [<command>]
    {CP} get_state
    {CP} run_game [<name>]
    {CP} list_games
    {CP} force_idle
    {CP} edit_config <val> (-s|-a|-r) <keys>...
    {CP} manual_interaction <keys_and_values>...

Options:
    <command>           command to ask for more information on
    <name>              name of game to launch
    <val>               value to be edited in
    -s                  set the value into config with that key path
    -a                  add the value to a list at the key path
    -r                  remove the value from a list at the key path
    <keys>              path of keys to navigate through config with, starting with 
    <keys_and_values>   alternating keys and value to set to those keys for the interaction
"""
type GameOperatorState = Literal[
    'idle',
    'run_individual_game',
    'run_tourney'
]
GAME_OPERATOR_STATES:set[GameOperatorState] = set(get_args(GameOperatorState))
class CommandExit(Exception):
    ...
class Response(CommandExit):
    ...
class ArgumentError(CommandExit):
    ...
class StateIncompatibility(CommandExit):
    def __init__(self,state:GameOperatorState, not_state:Iterable[GameOperatorState]):
        super().__init__(f"Current state '{state}' cannot be {wordify_iterable(not_state,'or')} for the purposes of this command.")


T = TypeVar('T',bound=Callable)
def command(func:T) -> T:
    func._is_command = True
    return func
def inherit_doc_string(from_func:T) -> Callable[[T],T]:
    def wrapper(func:T) -> T:
        func.__doc__ = from_func.__doc__
        return func
    return wrapper


class Game_Operator(Interface_Operator):
    class Command_Structure():
        def __init__(self,go:Optional['Game_Operator'] = None):
            self._funcs:dict[str,Callable] = {}
            if go is not None:
                self.bind_to(go)
        async def launch_commands(self,command_data:dict[str,Any]):
            for name,func in self._funcs.items():
                if command_data[name]:
                    #go:Game_Operator = func.__self__
                    spec = inspect.getfullargspec(func)
                    types:dict[str,Any] = get_type_hints(func)
                    kwargs = {}
                    for arg in spec.args:
                        if arg in ('self','cls'):
                            continue
                        arg_name = arg
                        tp = types[arg]
                        if get_origin(tp) == Literal:
                            options = get_args(tp)
                            key = get_first(
                                option for option in options
                                if command_data[f"-{option}"]
                            )
                            kwargs[arg] = key
                            continue
                        if tp in (
                            str,
                            Sequence[str],
                            Optional[str]
                        ):
                            arg_name = f"<{arg_name}>"
                        elif tp == bool:
                            arg_name = f"-{arg_name}"
                        kwargs[arg] = command_data[arg_name]
                    await func(**kwargs)
        def bind_to(self,go:'Game_Operator'):
            attribute_names = dir(go)
            for attribute_name in attribute_names:
                func = getattr(go,attribute_name)
                if hasattr(func,"_is_command") and getattr(func,"_is_command"):
                    self._funcs[func.__name__] = func
    def __init__(self,gi:Game_Interface):
        super().__init__(gi)
        self.command_structure = Game_Operator.Command_Structure(self)
        self.state:GameOperatorState = 'idle'
        self.game:Optional[Game] = None
        self.run_task:Optional[asyncio.Task] = None
        self.bind()
    @command
    async def help(self,command:Optional[str]):
        """responds with the doc-string of the respective command, or with the overall commands if not command is given

        Args:
            command: name of the command to request help, if not given requests help on all

        Raises:
            Response: responds with the overall doc-string if command is not given
            ArgumentError: does not accept non-existent commands
            Response: responds with the doc-string for the given command
        """
        if command is None:
            raise Response(COMMAND_DOCSTRING)
        else:
            if command not in self.command_structure._funcs.keys():
                raise ArgumentError(f"Command '{command}' does not exist.")
            doc = self.command_structure._funcs[command].__doc__
            raise Response(f"**{command}**:\n{doc}")
    @inherit_doc_string(help)
    @command
    async def h(self,command:Optional[str]):
        return await self.help(command)
    @command
    async def get_state(self):
        """responds with the current state of the game operator

        Raises:
            Response: responds with the current state of the game operator
        """
        raise Response(f"Current state: {self.state}.")
    @command
    async def run_game(self,name:Optional[str]):
        """runs the given game, or a random game if none given

        Args:
            name: name of the game to play; case insensitive; can be just the first letters of each word in the game's name; if not given the game will be randomly chosen

        Raises:
            StateIncompatibility: if game is not 'idle' and ready to play
            ArgumentError: if the game could not be found
        """
        if not self.state == 'idle':
            raise StateIncompatibility(self.state,GAME_OPERATOR_STATES - set(('idle',)))
        game_type:type[Game]
        if name is None:
            game_type = random_game()
        else:
            try:
                game_type = search_games(name)
            except IndexError:
                raise ArgumentError(f"Game '{name}' does not exist.")
        self.game = game_type(self.gi)
        self.state = 'run_individual_game'
        self.run_task = asyncio.create_task(self.game.run())
        await asyncio.wait([self.run_task])
        self.run_task = None
        try:
            await self.game.basic_send_placement(self.game.generate_placements())
        except Exception as e:
            await self.say("There has been an error in generating your placements. Many apologies.")
            logger.error(f"Game '{self.game}' errored trying to generate placements : {e}.")
        await self.gi.reset()
        self.bind()#re-add this function to game_interface's on action list
        self.state = 'idle'
    @command
    async def force_idle(self):
        """forces the game operator to return to an idle state

        Raises:
            StateIncompatibility: if the state is already 'idle'
            Response: responds with a confirmation
        """
        if self.state == 'idle':
            raise StateIncompatibility(self.state,['idle'])
        else:
            if self.run_task is not None:
                self.run_task.cancel()
                self.run_task = None
            self.state = 'idle'
            raise Response("The running task has been cancelled.")
    @command
    async def list_games(self):
        """responds with the list of games that are marked as ready to play (the same set random_game uses)

        Raises:
            Response: the list of games
        """
        raise Response(f"The current play-ready games are: {wordify_iterable(valid_games)}.")
    @command
    async def edit_config(self,val:str,mode:Literal['s','a','r'],keys:Sequence[str]):
        """edits the saved local config (it will not necessarily apply without a restart)

        Args:
            val: value to modify in
            mode: s to set, a to add to list, r to remove from list
            keys: chain of keys to traverse in the config

        Raises:
            Response: confirmation message
            ArgumentError: if config cannot be edited in the described way
        """
        cmd:ConfigAction = 'set'
        if mode == 'r':
            cmd = 'remove'
        elif mode == 'a':
            cmd = 'add'
        try:
            config_edit(list(keys),cmd,val)
            raise Response("Successfully edited config.")
        except ConfigError as e:
            raise ArgumentError(
                f"Failed to edit config:\n{e}"
            )
    @command
    async def manual_interaction(self,keys_and_values:Sequence[str]):
        """creates an interaction and sends it to the game interface

        Args:
            keys_and_values: a list of alternating keys and values

        Raises:
            ArgumentError: if there are an uneven number of keys_and_values
            ArgumentError: if any provided keys are not permitted
            ArgumentError: if the command string was included in the interaction
        """
        return
        if len(keys_and_values)%2 != 0:
            raise ArgumentError(f"There must be an even number of keys_and_values, there are {len(keys_and_values)}.")
        types:dict[str,type[Any]] = get_type_hints(Interaction.__init__)
        val_strs:dict[str,str] = {
            keys_and_values[i]:keys_and_values[i+1] 
            for i in range(int(len(keys_and_values)/2))
        }
        invalid_keys = set(val_strs) - set(types)
        if invalid_keys:
            raise ArgumentError(f"These keys are not permitted: {invalid_keys}")
        vals:dict[str,Any] = {}
        for key_str,val_str in val_strs.items():
            try:
                vals[key_str] = literal_eval(val_str)
            except SyntaxError:
                vals[key_str] = val_str
        interaction_type:str = 'interaction_type'
        if interaction_type not in vals:
            vals[interaction_type] = 'send_message'
        interaction = Interaction(**vals)
        if interaction.content is not None:
            if CP in interaction.content:
                raise ArgumentError(f"Containing '{CP}' in your content is not permitted.")
        await self.gi._trigger_action(interaction)
    def bind(self):
        @self.gi.watch(filter=lambda interaction: isinstance(interaction.content,Send_Text),owner = self)
        async def recv_command(interaction:Interaction):
            assert isinstance(interaction.content,Send_Text)
            if interaction.content.text.startswith(config['command_prefix']):
                if interaction.at_address is None:
                    async def send(content:str):
                        await self.sender(Text_Only(text=content))
                    try:
                        command_data = docopt(COMMAND_DOCSTRING,list(shlex.shlex(interaction.content.text[len(CP):],punctuation_chars=True)),default_help=False)
                    except DocoptExit as e:
                        await send(
                            "Our interpreter was unable to interpret this command of:\n" +
                            f"'{interaction.content.text}'\n" +
                            e.__str__()
                        )
                        return
                    try:
                        await self.command_structure.launch_commands(command_data)
                    except CommandExit as e:
                        await send(e.args[0])