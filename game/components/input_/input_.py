import asyncio
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, Generic, Iterable, Required, TypedDict, Unpack

from typing_extensions import TypeVar

from game.components.input_.input_name import InputNameVar
from game.components.input_.response_validator import ResponseValidator, not_none
from game.components.interface_component import Interface_Component
from game.components.participant import ParticipantVar
from smart_text import TextLike
from utils.logging import get_logger
from utils.types import Grouping, SimpleCallback

if TYPE_CHECKING:
    from game.components.game_interface import Game_Interface
    from game.components.input_.completion_criteria import Completion_Criteria
    from game.components.input_.responses import Responses
    from game.components.input_.status_display import Status_Display

logger = get_logger(__name__)

WAIT_UNTIL_DONE_CHECK_TIME = 5

InputDataTypeVar = TypeVar('InputDataTypeVar')


class InputArgs(
    Generic[InputDataTypeVar,InputNameVar,ParticipantVar],
    TypedDict,
    total = False
    ):
    response_validator:ResponseValidator[InputDataTypeVar,ParticipantVar]
    completion_criteria:'Completion_Criteria[InputDataTypeVar,InputNameVar,ParticipantVar]'
    participants:Required[Grouping[ParticipantVar]]
    on_updates:Iterable['SimpleCallback[Input[InputDataTypeVar,InputNameVar,ParticipantVar]]']
    identifier:TextLike

class RunArgs(
    TypedDict,
    total = False
):
    max_time:float
    notification_times:tuple[float,...]

class Input(
    Generic[InputDataTypeVar,InputNameVar,ParticipantVar],
    Interface_Component
    ):
    def __init__(self,gi:'Game_Interface',**kwargs:Unpack[InputArgs[InputDataTypeVar,InputNameVar,ParticipantVar]]):
        Interface_Component.__init__(self,gi)
        self.participants: Grouping[ParticipantVar] = kwargs['participants']
        self.response_validator:ResponseValidator[InputDataTypeVar,ParticipantVar] = not_none
        self.completion_criteria:'Completion_Criteria[InputDataTypeVar,InputNameVar,ParticipantVar]' = All_Valid_Responded(self)
        self.on_updates:set['SimpleCallback[Input[InputDataTypeVar,InputNameVar,ParticipantVar]]'] = set()
        self.identifier:TextLike|None = None
        if 'response_validator' in kwargs:
            self.response_validator = kwargs['response_validator']
        if 'completion_criteria' in kwargs:
            self.completion_criteria = kwargs['completion_criteria']
        if 'on_updates' in kwargs:
            self.on_updates.update(kwargs['on_updates'])
        else:
            self.on_updates.add(
                Status_Display[InputDataTypeVar,InputNameVar,ParticipantVar]()
            )
        if 'identifier' in kwargs:
            self.identifier = kwargs['identifier']
        self.responses:Responses[InputDataTypeVar,ParticipantVar] = Responses(self)
    async def setup(self):
        logger.info(f"{self} setting up.")
    async def unsetup(self):
        logger.info(f"{self} undoing setup.")
    async def wait_until_done(self):
        logger.info(f"{self} waiting until is_done.")
        while not self.is_done():
            await asyncio.sleep(WAIT_UNTIL_DONE_CHECK_TIME)
    def is_done(self) -> bool:
        return self.responses.all_valid()
    async def run(self):
        await self.setup()
        await self.wait_until_done()
        await self.unsetup()
    async def update_on_updates(self):
        for on_update in self.on_updates:
            if iscoroutinefunction(on_update):
                await on_update(self)
            else:
                on_update(self)
    def on_update(self,callback:'SimpleCallback[Input[InputDataTypeVar,InputNameVar,ParticipantVar]]'):
        self.on_updates.add(callback)
    def reset(self):
        self.responses = Responses(self)

from game.components.input_.completion_criteria import All_Valid_Responded  # noqa: E402
from game.components.input_.responses import Responses  # noqa: E402
from game.components.input_.status_display import Status_Display # noqa: E402