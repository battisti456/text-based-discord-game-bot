from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Hashable

if TYPE_CHECKING:
    from game.components.send.interaction import InteractionFilter, Interaction

@dataclass(frozen=True)
class Address():
    key:frozenset[Hashable] = frozenset()
    def get_filter(self) -> 'InteractionFilter[Any]':
        def _(interaction:'Interaction') -> bool:
            return interaction.at_address == self
        return _
