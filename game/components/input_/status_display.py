from dataclasses import dataclass
from game.components.send import Address
from typing import TYPE_CHECKING, Generic

from game.components.participant import ParticipantVar
from game.components.input_._input_names import InputNameVar

if TYPE_CHECKING:
    from game.components.input_.input_ import Input, InputDataTypeVar

@dataclass(frozen=True)
class Status_Display(Generic['InputDataTypeVar',InputNameVar,ParticipantVar]):
    display_address:Address
    async def display(self,pi:'Input[InputDataTypeVar,InputNameVar,ParticipantVar]'):
        raise NotImplementedError()
