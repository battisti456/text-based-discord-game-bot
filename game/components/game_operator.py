import asyncio
import sys
from typing import Literal, Optional, Any, get_type_hints
from ast import literal_eval
import shlex

import git
from docopt import DocoptExit, docopt

import game.games
from config.config import config
from config.config_tools import ConfigAction, ConfigError
from config.config_tools import edit as config_edit
from game.components.game_interface import Game_Interface
from game.components.interaction import Interaction
from game.components.interface_operator import Interface_Operator
from game.game import Game
from game.games import games, random_game
from utils.grammar import wordify_iterable

CP = config['command_prefix']
COMMAND_DOCSTRING= f"""
Usage:
    {CP} h | help | -h | --help
    {CP} get_state
    {CP} run_game [<name>]
    {CP} list_games
    {CP} stop_run
    {CP} restart_server
    {CP} update_server
    {CP} edit_config <val> (-s|-a|-r) <keys>...
    {CP} manual_interaction [<key>=<value>]...

Options:
    <name>          name of game to launch
    <val>           value to be edited in
    -s              set the value into config with that key path
    -a              add the value to a list at the key path
    -r              remove the value from a list at the key path
    <keys>          path of keys to navigate through config with, starting with 
    <key>=<value>   a key value pair to be stored
    config name
"""


type GameOperatorState = Literal[
    'idle',
    'run_individual_game',
    'run_tourney'
]

class Game_Operator(Interface_Operator):
    def __init__(self,gi:Game_Interface):
        super().__init__(gi)

        self.state:GameOperatorState = 'idle'
        self.game:Optional[Game] = None
        self.run_task:Optional[asyncio.Task] = None
        self.bind()
    def bind(self):
        @self.gi.on_action('send_message',self)
        async def recv_command(interaction:Interaction):
            if interaction.content is not None:
                if interaction.content.startswith(config['command_prefix']):
                    if interaction.reply_to_message_id is None:
                        async def send(content:str):
                            await self.send(interaction.reply(content))
                        try:
                            args = docopt(COMMAND_DOCSTRING,list(shlex.shlex(interaction.content[len(CP):])),default_help=False)
                        except DocoptExit as e:
                            await send(
                                "Our interpreter was unable to interpret this command of:\n" +
                                f"'{interaction.content}'\n" +
                                e.__str__()
                            )
                            return
                        if any(args[help_option] for help_option in ["h","help","-h","--help"]):
                            await send(COMMAND_DOCSTRING)
                        elif args['get_state']:
                            await send(f"The current state is '{self.state}'.")
                        elif args['run_game']:
                            if not self.state == 'idle':
                                await send("I am too busy to do this right now.")
                                return
                            game_type:type[Game]
                            if args['<name>'] is None:
                                game_type = random_game()
                            else:
                                #options = list(game_type for game_type in games if game_type.__name__ == args['<name>'])
                                #if len(options) == 0:
                                #    await send(f"'{args['<name>']}' is not the name of a valid game.")
                                #    return
                                #game_type = options[0]
                                try:
                                    game_type = getattr(game.games,args['<name>'])
                                    assert issubclass(game_type,Game)
                                except AssertionError:
                                    await send(f"'{args['<name>']}' is not the name of a valid game.")
                                    return
                                
                            self.game = game_type(self.gi)
                            self.state = 'run_individual_game'
                            self.run_task = asyncio.create_task(self.game.run())
                            await asyncio.wait([self.run_task])
                            self.run_task = None
                            await self.game.basic_send_placement(self.game.generate_placements())
                            await self.gi.reset()
                            self.bind()#re-add this function to game_interface's on action list
                            self.state = 'idle'
                        elif args['list_games']:
                            await send(
                                "Our current games are: " + wordify_iterable(list(game_type.__name__ for game_type in games)) + "."
                            )
                        elif args['stop_run']:
                            if self.run_task is None:
                                await send("There is nothing currently running.")
                            else:
                                self.run_task.cancel()
                                self.run_task = None
                                await send("The running task has been cancelled.")
                        elif args['restart_server']:
                            sys.exit(0)
                        elif args['update_server']:
                            local_git = git.Git()
                            info_text = local_git.pull()
                            await send(
                                f"{info_text}\nFor some changes you may need to restart the server."
                            )
                        elif args['edit_config']:
                            cmd:ConfigAction = 'set'
                            if args['-r']:
                                cmd = 'remove'
                            elif args['-a']:
                                cmd = 'add'
                            try:
                                config_edit(args['<keys>'],cmd,args['<val>'])
                                await send("Successfully edited config.")
                            except ConfigError as e:
                                await send(
                                    f"Failed to edit config:\n{e}"
                                )
                        elif args['manual_interaction']:
                            types:dict[str,type[Any]] = get_type_hints(Interaction.__init__)
                            print(args['<key>=<value>'])
                            val_strs:dict[str,str] = {}
                            kvargs = args['<key>=<value>']
                            num_args = int(len(kvargs)/3)
                            if num_args != len(kvargs)/3:
                                await send(f"I interpreted this as {kvargs}, but if they were, it would need to be diviable by 3")
                                return
                            for i in range(num_args):
                                val_strs[kvargs[i*3]] = kvargs[i*3+2]
                            invalid = set(val_strs) - set(types)
                            if invalid:
                                await send(f"these keys are not permitted: {invalid}")
                                return
                            vals:dict[str,Any] = {}
                            for key_str,val_str in val_strs.items():
                                try:
                                    vals[key_str] = literal_eval(val_str)
                                except SyntaxError:
                                    vals[key_str] = val_str
                            """#type checking wouldn't work for id's, I don't think
                            for key in vals:
                                try:
                                    check_type(vals[key],types[key])
                                except TypeCheckError:
                                    await send(f"on key {key} your value registered as type {type(vals[key])} which is not permitted in {types[key]}")
                                    return"""
                            interaction_type:str = 'interaction_type'
                            if interaction_type not in vals:
                                vals[interaction_type] = 'send_message'
                            interaction = Interaction(**vals)
                            if interaction.content is not None:
                                if CP in interaction.content:
                                    await send(f"containing '{CP}' in your content is not permitted")
                                    return
                            await self.gi._trigger_action(interaction)
                                
                                
                                
