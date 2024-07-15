import asyncio
from typing import Iterable, Optional

from game.components.input_.input_ import Input, WAIT_UNTIL_DONE_CHECK_TIME
from utils.logging import get_logger

logger = get_logger(__name__)

async def run(
        *inputs:Input,
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
