from dataclasses import dataclass
from game.components.send import Address
from typing import TYPE_CHECKING, Generic

if TYPE_CHECKING:
    from game.components.player_input.player_input import PlayerInputVar

@dataclass(frozen=True)
class Status_Display(Generic['PlayerInputVar']):
    display_address:Address
    async def display(self,pi:'PlayerInputVar'):
        raise NotImplementedError()
