from dataclasses import dataclass
from typing import Generic

from game.components.input_.input_ import Input, InputDataTypeVar
from game.components.input_.input_name import InputNameVar
from game.components.participant import ParticipantVar
from game.components.send import Address


@dataclass(frozen=True)
class Status_Display(Generic[InputDataTypeVar,InputNameVar,ParticipantVar]):
    display_address:Address
    async def display(self,pi:'Input[InputDataTypeVar,InputNameVar,ParticipantVar]'):
        raise NotImplementedError()
