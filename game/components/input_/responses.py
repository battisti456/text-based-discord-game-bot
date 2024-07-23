from collections import OrderedDict
from typing import Any, Generic, Iterator, override

from game.components.input_.input_ import Input, InputDataTypeVar
from game.components.participant import ParticipantVar
from utils.common import get_first


class Responses(
    Generic[InputDataTypeVar,ParticipantVar],
    OrderedDict[ParticipantVar,InputDataTypeVar|None]
):
    def __init__(self,pi:'Input[InputDataTypeVar,Any,ParticipantVar]'):
        OrderedDict.__init__(self)
        self.pi: 'Input[InputDataTypeVar, Any, ParticipantVar]' = pi
        for participant in self.pi.participants:
            self[participant] = None
    @property
    def last(self) -> tuple[ParticipantVar,InputDataTypeVar|None]:
        return get_first(self.items())
    @override
    def __setitem__(self, key: ParticipantVar, value: InputDataTypeVar | None) -> None:
        super().__setitem__(key, value)
        self.move_to_end(key,False)
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
    def responses(self) -> Iterator[tuple[ParticipantVar,InputDataTypeVar]]:
        return (
            (participant,response)
            for participant,response in self.items()
            if response is not None
        )
    def valid_responses(self) -> Iterator[tuple[ParticipantVar,InputDataTypeVar]]:
        return (
            (participant,response)
            for participant,response in self.items()
            if self.pi.response_validator(participant,response)[0]
            and response is not None
        )
    def all_responded(self) -> bool:
        return all(response is not None for response in self.values())
    def all_valid(self) -> bool:
        return all(
            response is not None 
            and self.pi.response_validator(participant,response)[0] 
            for participant,response in self.items()
        )
    def has_response(self,participant:ParticipantVar) -> bool:
        return participant in self.keys() and self[participant] is not None
    def has_valid_response(self,participant:ParticipantVar) -> bool:
        return participant in self.keys() and self[participant] is not None and self.pi.response_validator(participant,self[participant])[0]