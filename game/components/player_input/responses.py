from typing import TYPE_CHECKING, Generic, Iterator, TypeVar

from game.components.participant import ParticipantVar

if TYPE_CHECKING:
    from game.components.player_input.player_input import Player_Input

T = TypeVar('T')

class Responses(
    Generic[T,ParticipantVar],
    dict[ParticipantVar,T|None]
):
    def __init__(self,pi:'Player_Input[T,ParticipantVar]'):
        dict.__init__(self)
        self.pi: 'Player_Input[T, ParticipantVar]' = pi
    def did_not_respond(self) -> Iterator[ParticipantVar]:
        return (participant for participant,response in self.items() if response is None)
    def did_respond(self) -> Iterator[ParticipantVar]:
        return (participant for participant,response in self.items() if response is not None)
    def did_respond_valid(self) -> Iterator[ParticipantVar]:
        return (
            participant for  participant,response in self.items()
            if self.pi.response_validator(participant,response)[0]
            and response is not None
            )
    def responses(self) -> Iterator[tuple[ParticipantVar,T]]:
        return (
            (participant,response)
            for participant,response in self.items()
            if response is not None
        )
    def valid_responses(self) -> Iterator[tuple[ParticipantVar,T]]:
        return (
            (participant,response)
            for participant,response in self.items()
            if self.pi.response_validator(participant,response)[0]
            and response is not None
        )