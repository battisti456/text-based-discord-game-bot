from types import ModuleType
from typing import TYPE_CHECKING

import importlib

from game.game import Game, import_games

PATH = "game\\game_bases"
modules:dict[str,ModuleType] = {}
game_bases:dict[str,type[Game]] = {}
import_games(
    PATH,
    modules,
    game_bases
)

def reload():
    for name in modules:
        importlib.reload(modules[name])
    import_games(
        PATH,
        modules,\
        game_bases
    )

from game.game_bases.elimination_base import Elimination_Base
from game.game_bases.card_base import Card_Base
from game.game_bases.dictionary_base import Dictionary_Base
from game.game_bases.trivia_base import Trivia_Base
from game.game_bases.rounds_with_points_base import Rounds_With_Points_Base
from game.game_bases.random_image_base import Random_Image_Base
from game.game_bases.basic_secret_message_base import Basic_Secret_Message_Base
