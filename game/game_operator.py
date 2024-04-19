from config import config

from typing import Literal, TypedDict, Optional
from docopt import docopt, DocoptExit

from game.game_interface import Game_Interface
from game.interface_operator import Interface_Operator
from game.interaction import Interaction
from game.game import Game
from game.games import random_game, games
from game.grammer import wordify_iterable

CP = config['command_prefix']
COMMAND_DOCSTRING= f"""

Usage:
    {CP} h | help | -h | --help
    {CP} get_state
    {CP} run_game [<name>]
    {CP} list_games

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

        @self.gi.on_action('send_message',self)
        async def recv_command(interaction:Interaction):
            if not interaction.content is None:
                if interaction.content.startswith(config['command_prefix']):
                    if interaction.reply_to_message_id is None:
                        try:
                            args = docopt(COMMAND_DOCSTRING,interaction.content[len(CP):],default_help=False)
                        except DocoptExit as e:
                            await self.send(interaction.reply(
                                "Our interpreter was unable to interpret this command of:\n" +
                                f"'{interaction.content}'\n" +
                                e.__str__()
                            ))
                            return
                        if any(args[help_option] for help_option in ["h","help","-h","--help"]):
                            await self.send(interaction.reply(COMMAND_DOCSTRING))
                        elif args['get_state']:
                            await self.send(interaction.reply(f"The current state is '{self.state}'."))
                        elif args['run_game']:
                            if not self.state == 'idle':
                                await self.send(interaction.reply("I am too busy to do this right now."))
                                return
                            game_type:type[Game]
                            if args['<name>'] is None:
                                game_type = random_game()
                            else:
                                options = list(game_type for game_type in games if game_type.__name__ == args['<name>'])
                                if len(options) == 0:
                                    await self.send(interaction.reply(f"'{args['<name>']}' is not the name of a valid game."))
                                    return
                                game_type = options[0]
                            self.game = game_type(self.gi)
                            self.state = 'run_individual_game'
                            await self.game.run()
                            await self.game.basic_send_placement(self.game.generate_placements())
                            self.state = 'idle'
                        elif args['list_games']:
                            await self.send(interaction.reply(
                                "Our current games are: " + wordify_iterable(game_type.__name__ for game_type in games) + "."
                            ))





