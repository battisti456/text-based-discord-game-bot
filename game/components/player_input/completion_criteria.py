from typing import TYPE_CHECKING, override, Generic, Any

from game.components.player_input.player_input import Player_Input

if TYPE_CHECKING:
    from game.components.player_input.player_input import Player_Input, PlayerInputVar

class Completion_Criteria(Generic[PlayerInputVar]):
    def __init__(self,pi:PlayerInputVar):
        self.pi = pi
    def __call__(self) -> bool:
        raise NotImplementedError()

class All_Valid_Responded(Completion_Criteria[Player_Input[Any,Any]]):
    @override
    def __call__(self) -> bool:
        return self.pi.responses.all_valid()

class All_Responded(Completion_Criteria[Player_Input[Any,Any]]):
    @override
    def __call__(self) -> bool:
        return self.pi.responses.all_responded()

