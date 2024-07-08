from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.components.participant import Player

@dataclass(frozen=True)
class Address():
    for_players:frozenset['Player'] = field(default_factory=frozenset,kw_only=True)
    "if empty, assumes all"
