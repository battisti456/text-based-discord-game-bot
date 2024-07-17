from typing import TYPE_CHECKING, Literal, Unpack, override

from typeguard import check_type

import game.components.send.interaction as interactions
from game.components.input_.input_ import (
    Input,
    InputArgs,
)
from game.components.input_.input_name import InputNameVar
from game.components.participant import Player
from game.components.send import (
    Interaction,
    InteractionContentVar,
    InteractionFilter,
    no_filter,
)
from utils.logging import get_logger

if TYPE_CHECKING:
    from game.components.game_interface import Game_Interface

logger= get_logger(__name__)

class InteractionReceivingPlayerInputArgs(
    InputArgs[InteractionContentVar,InputNameVar,Player],
    total = False,
):
    interaction_filter:InteractionFilter[InteractionContentVar]
    allow_edits:bool


class Interaction_Receiving_Player_Input(
    Input[InteractionContentVar,InputNameVar,Player]
    ):
    def __init__(
            self,
            gi:'Game_Interface',
            **kwargs:Unpack[InteractionReceivingPlayerInputArgs[
                InteractionContentVar,
                InputNameVar]]
        ):
        super().__init__(gi,**kwargs)
        self._interaction_filter:InteractionFilter[InteractionContentVar] = no_filter
        self.allow_edits:bool = True
        if 'interaction_filter' in kwargs:
            self._interaction_filter = kwargs['interaction_filter']
        if 'allow_edits' in kwargs:
            self.allow_edits = kwargs['allow_edits']
    def interaction_filter(self,interaction:Interaction) -> bool:
        try:
            check_type(interaction,InteractionContentVar)
            if not self._interaction_filter(interaction):
                logger.debug(f"{self} rejected {interaction} for failing the provided interaction filter.")
                return False
            if not self.allow_edits and self.responses.has_valid_response(interaction.by_player):
                logger.debug(f"{self} rejected {interaction} because edits are not currently allowed, and {interaction.by_player} already has a valid response of {self.responses[interaction.by_player]}")
                return False
            return True
        except TypeError:
            logger.debug(f"{self} rejected {interaction} for failing the content type check.")
            return False
    async def on_interact(self,interaction:Interaction[InteractionContentVar]):
        self.responses[interaction.by_player] = interaction.content
    @override
    async def setup(self):
        await super().setup()
        self.gi.watch(self.interaction_filter,self)(self.on_interact)
    @override
    async def unsetup(self):
        await super().unsetup()
        self.gi.purge_actions(self)

class TextInputArgs(InteractionReceivingPlayerInputArgs[interactions.Send_Text,Literal['Text_Input']]):
    ...

class Text_Input(Interaction_Receiving_Player_Input[interactions.Send_Text,Literal['Text_Input']]):
    def __init__(self, gi: 'Game_Interface', **kwargs: Unpack[TextInputArgs]):
        super().__init__(gi, **kwargs)

class SelectInputArgs(InteractionReceivingPlayerInputArgs[interactions.Select_Options,Literal['Select_Input']]):
    ...

class Select_Input(Interaction_Receiving_Player_Input[interactions.Select_Options,Literal['Select_Input']]):
    def __init__(self, gi: 'Game_Interface', **kwargs: Unpack[SelectInputArgs]):
        super().__init__(gi, **kwargs)

class CommandInputArgs(InteractionReceivingPlayerInputArgs[interactions.Command,Literal['Command_Input']]):
    ...

class Command_Input(Interaction_Receiving_Player_Input[interactions.Command,Literal['Command_Input']]):
    def __init__(self, gi: 'Game_Interface', **kwargs: Unpack[CommandInputArgs]):
        super().__init__(gi, **kwargs)