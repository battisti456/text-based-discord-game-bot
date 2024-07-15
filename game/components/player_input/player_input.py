from typing import Generic, TypeVar, TypedDict, Unpack

from game.components.interface_component import Interface_Component
from game.components.game_interface import Game_Interface
from game.components.participant import ParticipantVar
from game.components.player_input.response_validator import ResponseValidator, not_none
from game.components.player_input.responses import Responses
from game.components.send import Interaction, InteractionContentVar

T = TypeVar('T')

class PlayerInputArgs(
    Generic[T,ParticipantVar],
    TypedDict,
    total = False
    ):
    response_validator:ResponseValidator[T,ParticipantVar]

class Player_Input(
    Generic[T,ParticipantVar],
    Interface_Component
    ):
    def __init__(self,gi:Game_Interface,**kwargs:Unpack[PlayerInputArgs[T,ParticipantVar]]):
        Interface_Component.__init__(self,gi)
        self.responses:Responses[T,ParticipantVar] = Responses(self)
        self.response_validator:ResponseValidator[T,ParticipantVar] = not_none
        if 'response_validator' in kwargs:
            self.response_validator = kwargs['response_validator']

class InteractionReceivingPlayerInputArgs(
    PlayerInputArgs[InteractionContentVar,ParticipantVar],
    total = False
):
    ...

class Interaction_Receiving_Player_Input(
    Player_Input[InteractionContentVar,ParticipantVar]
    ):
    def __init__(
            self,
            gi:Game_Interface,
            **kwargs:Unpack[InteractionReceivingPlayerInputArgs[InteractionContentVar,ParticipantVar]]
        ):
        super().__init__(gi,**kwargs)