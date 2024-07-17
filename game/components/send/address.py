from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from game.components.participant import Player
    from game.components.send.interaction import InteractionFilter, Interaction

@dataclass(frozen=True)
class Address():
    for_players:frozenset['Player'] = field(default_factory=frozenset,kw_only=True)
    "if empty, assumes all"
    def get_filter(self) -> 'InteractionFilter[Any]':
        def _(interaction:'Interaction') -> bool:
            return interaction.at_address == self
        return _
