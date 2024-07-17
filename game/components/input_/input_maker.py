from typing import TYPE_CHECKING
from dataclasses import dataclass, field
from functools import partial

from game.components.input_.interaction_input import (
    Command_Input,
    Select_Input,
    Text_Input,
)
from game.components.input_.run import run

if TYPE_CHECKING:
    from game.components.game_interface import Game_Interface

@dataclass
class Input_Maker():
    gi:'Game_Interface' = field()
    select = partial(Select_Input,gi)
    text = partial(Text_Input,gi)
    command = partial(Command_Input,gi)
    run = run
