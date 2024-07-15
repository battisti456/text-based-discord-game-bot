from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils.types import PlayerId

@dataclass(frozen=True)
class Address():
    for_players:frozenset['PlayerId'] = field(default_factory=frozenset,kw_only=True)
    "if empty, assumes all"
