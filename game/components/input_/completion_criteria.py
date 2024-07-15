from typing import TYPE_CHECKING, override, Generic, Any

from game.components.input_.input_ import Input, InputDataTypeVar
from game.components.input_.input_name import InputNameVar
from game.components.participant import ParticipantVar

if TYPE_CHECKING:
    from game.components.input_.input_ import Input

class Completion_Criteria(Generic[InputDataTypeVar,InputNameVar,ParticipantVar]):
    def __init__(self,pi:Input[InputDataTypeVar,InputNameVar,ParticipantVar]):
        self.pi = pi
    def __call__(self) -> bool:
        raise NotImplementedError()

class All_Valid_Responded(Completion_Criteria[Any,Any,Any]):
    @override
    def __call__(self) -> bool:
        return self.pi.responses.all_valid()

class All_Responded(Completion_Criteria[Any,Any,Any]):
    @override
    def __call__(self) -> bool:
        return self.pi.responses.all_responded()

