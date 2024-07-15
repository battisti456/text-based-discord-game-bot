import asyncio
from typing import Generic, Required, Sequence, TypedDict, Unpack

from typing_extensions import TypeVar

from game.components.game_interface import Game_Interface
from game.components.interface_component import Interface_Component
from game.components.participant import ParticipantVar
from game.components.player_input._input_names import InputNameVar
from game.components.player_input.completion_criteria import (
    All_Valid_Responded,
    Completion_Criteria,
)
from game.components.player_input.response_validator import ResponseValidator, not_none
from game.components.player_input.responses import Responses
from game.components.player_input.status_display import Status_Display
from utils.logging import get_logger
from utils.types import Grouping

logger = get_logger(__name__)

WAIT_UNTIL_DONE_CHECK_TIME = 5

InputDataTypeVar = TypeVar('InputDataTypeVar')

class InputArgs(
    Generic[InputDataTypeVar,InputNameVar,ParticipantVar],
    TypedDict,
    total = False
    ):
    response_validator:ResponseValidator[InputDataTypeVar,ParticipantVar]
    completion_criteria:Completion_Criteria[InputDataTypeVar,InputNameVar,ParticipantVar]
    participants:Required[Grouping[ParticipantVar]]
    status_displays:Sequence[Status_Display[InputDataTypeVar,InputNameVar,ParticipantVar]]

class Input(
    Generic[InputDataTypeVar,InputNameVar,ParticipantVar],
    Interface_Component
    ):
    def __init__(self,gi:Game_Interface,**kwargs:Unpack[InputArgs[InputDataTypeVar,InputNameVar,ParticipantVar]]):
        Interface_Component.__init__(self,gi)
        self.participants: Grouping[ParticipantVar] = kwargs['participants']
        self.response_validator:ResponseValidator[InputDataTypeVar,ParticipantVar] = not_none
        self.completion_criteria:Completion_Criteria[InputDataTypeVar,InputNameVar,ParticipantVar] = All_Valid_Responded(self)
        self.status_displays:Sequence[Status_Display[InputDataTypeVar,InputNameVar,ParticipantVar]] = tuple()
        if 'response_validator' in kwargs:
            self.response_validator = kwargs['response_validator']
        if 'completion_criteria' in kwargs:
            self.completion_criteria = kwargs['completion_criteria']
        if 'status_displays' in kwargs:
            self.status_displays = kwargs['status_displays']
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
    async def update_displays(self):
        for display in self.status_displays:
            await display.display(self)