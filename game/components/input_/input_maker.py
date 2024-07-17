import asyncio
from functools import partial
from typing import TYPE_CHECKING, Any, Iterable, Optional

from game.components.input_.input_ import WAIT_UNTIL_DONE_CHECK_TIME, Input
from game.components.input_.interaction_input import (
    Command_Input,
    Select_Input,
    Text_Input,
)
from utils.logging import get_logger

if TYPE_CHECKING:
    from game.components.game_interface import Game_Interface

logger  = get_logger(__name__)

class Input_Maker():
    def __init__(self,gi:'Game_Interface'):
        self.gi = gi
        self.select = partial(Select_Input,gi)
        self.text = partial(Text_Input,gi)
        self.command = partial(Command_Input,gi)
    @staticmethod
    async def run(
        *inputs:Input[Any,Any,Any],
        completion_sets:Optional[Iterable[Iterable[Input]]]=None
        ):
        if completion_sets is None:
            completion_sets = (inputs,)
        logger.info("Setting up multiple inputs.")
        for input_ in inputs:
            await input_.setup()
        is_done: bool = False
        while not is_done:
            await asyncio.sleep(WAIT_UNTIL_DONE_CHECK_TIME)
            done_map:dict[Input,bool] = {}
            for input_ in inputs:
                done_map[input_] = input_.is_done()
            for completion_set in completion_sets:
                if all(done_map[input_] for input_ in completion_set):
                    is_done = True
                    break
        logger.info("Unsetting up multiple inputs.")
        for input_ in inputs:
            await input_.unsetup()
        logger.info("Multi-run done.")
