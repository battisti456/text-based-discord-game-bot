import asyncio
from typing import TYPE_CHECKING, Generic, Iterable, Required, TypedDict, Unpack, override, Iterator
from time import time

from typing_extensions import TypeVar

from game.components.input_.input_name import InputNameVar
from game.components.input_.response_validator import ResponseValidator, not_none
from game.components.interface_component import Interface_Component
from game.components.participant import ParticipantVar
from game.components.send import make_sendable, Address
from game.components.send.address import Direct_Message
from smart_text import TextLike
from utils.logging import get_logger
from utils.types import Grouping, SimpleCallback
from game.components.participant import mention_participants, name_participants

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
    timeout:float
    reminders:Iterator[float]

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
        self.last_start_time:float|None = None
        self.last_end_time:float|None = None
        self.timeout:float|None = 259200#None
        self.reminders:Iterator[float] = (86400,86400,43200,21600,10800,3600).__iter__()#tuple().__iter__()
        if 'response_validator' in kwargs:
            self.response_validator = kwargs['response_validator']
        if 'completion_criteria' in kwargs:
            self.completion_criteria = kwargs['completion_criteria']
        if 'on_updates' in kwargs:
            self.on_updates.update(kwargs['on_updates'])
        if 'timeout' in kwargs:
            self.timeout = kwargs['timeout']
        if 'reminders' in kwargs:
            self.reminders = kwargs['reminders']
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
        await self.update_on_updates()
    async def unsetup(self):
        logger.info(f"{self} undoing setup.")
        await self.update_on_updates()
    async def wait_until_done(self):
        logger.info(f"{self} waiting until is_done.")
        assert self.last_start_time is not None
        timeout_check = lambda:True  # noqa: E731
        clean_up:list[Address] = []
        if self.timeout is not None:
            end_time = self.last_start_time+self.timeout
            clean_up.append(await self.send(text = f"You will need to have responded <t:{int(end_time)}:R>."))
            timeout_check = lambda:time()<end_time  # noqa: E731
        try:
            next_reminder = self.last_start_time + next(self.reminders)
        except StopIteration:
            next_reminder = None
        while not self.is_done() and timeout_check():
            if next_reminder is not None:
                if time() >= next_reminder:
                    logger.info(
                        f"{self}: Sending a reminder to {name_participants(self.responses.did_not_respond_valid())} at {next_reminder}."
                    )
                    for participant in self.responses.did_not_respond_valid():
                        clean_up.append(
                            await self.send(
                                address = await self.sender.generate_address(Direct_Message,participant),
                                text = f"{mention_participants((participant,))}, we are still waiting for you to respond!"
                            )
                        )
                    try:
                        next_reminder = next_reminder + next(self.reminders)
                    except StopIteration:
                        next_reminder = None
            await asyncio.sleep(WAIT_UNTIL_DONE_CHECK_TIME)
        #doesn't delete messages, just edits them to be blank. Do we even want messages deleted?
        # if timeout_check is not None:
        #     for address in clean_up:
        #         await self.send(
        #             address=address,
        #             text=""
        #         )
    def is_done(self) -> bool:
        return self.responses.all_valid()
    async def run(self):
        self.last_start_time = time()
        await self.setup()
        await self.wait_until_done()
        await self.unsetup()
        self.last_end_time = time()
    async def update_on_updates(self):
        for on_update in self.on_updates:
            val = on_update(self)
            try:
                await val#type:ignore
            except TypeError:
                ...
    def on_update(self,callback:'SimpleCallback[Input[InputDataTypeVar,InputNameVar,ParticipantVar]]'):
        self.on_updates.add(callback)
    def reset(self):
        self.responses = Responses(self)
    @override
    def __str__(self) -> str:
        return f'{self.__class__.__name__}({"" if self.identifier is None else self.identifier})'
    @override
    def __repr__(self) -> str:
        return str(self)


from game.components.input_.completion_criteria import All_Valid_Responded  # noqa: E402
from game.components.input_.responses import Responses  # noqa: E402
from game.components.input_.status_display import Status_Display # noqa: E402