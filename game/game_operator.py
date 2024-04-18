from config import config

from typing import Literal, TypedDict
from docopt import docopt

from game.game_interface import Game_Interface
from game.interface_operator import Interface_Operator
from game.interaction import Interaction

CP = config['command_prefix']
COMMAND_DOCSTRING= f"""

Usage:
    {CP} h | help | -h | --help

"""


type GameOperatorState = Literal[
    'wait',
    'run_game',
    'run_tourney'
]

class Game_Operator(Interface_Operator):
    def __init__(self,gi:Game_Interface):
        super().__init__(gi)



        @self.gi.on_action('send_message',self)
        async def recv_command(interaction:Interaction):
            if not interaction.content is None:
                if interaction.content.startswith(config['command_prefix']):
                    if interaction.reply_to_message_id is None:
                        args = docopt(COMMAND_DOCSTRING,interaction.content[len(CP):],default_help=False)
                        if any(args[help_option] for help_option in ["h","help","-h","--help"]):
                            await self.send(interaction.reply(COMMAND_DOCSTRING))
