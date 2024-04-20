from config import config

from typing import Literal, TypedDict, Optional
from types import ModuleType
from docopt import docopt, DocoptExit
import asyncio
from importlib import reload

from game.game_interface import Game_Interface
from game.interface_operator import Interface_Operator
from game.interaction import Interaction
from game.game import Game
from game.games import random_game, games
from game.grammer import wordify_iterable

import game.games
import game.game_bases

CP = config['command_prefix']
COMMAND_DOCSTRING= f"""

Usage:
    {CP} h | help | -h | --help #return this text
    {CP} get_state #return the current state of the game operator
    {CP} run_game [<name>] #runs the game given by <name>, or if nothing is given runs a random game
    {CP} list_games #lists all games available to run
    {CP} stop_run #stops the currently running function

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
            if not interaction.content is None:
                if interaction.content.startswith(config['command_prefix']):
                    if interaction.reply_to_message_id is None:
                        async def send(content:str):
                            await self.send(interaction.reply(content))
                        try:
                            args = docopt(COMMAND_DOCSTRING,interaction.content[len(CP):],default_help=False)
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
                                options = list(game_type for game_type in games if game_type.__name__ == args['<name>'])
                                if len(options) == 0:
                                    await send(f"'{args['<name>']}' is not the name of a valid game.")
                                    return
                                game_type = options[0]
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






