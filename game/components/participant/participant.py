from dataclasses import dataclass
from typing import override

from smart_text import TextLike
from utils.grammar.pronoun_set import COMMON_PRONOUNS, Pronoun_Set
from utils.types import GS


@dataclass(frozen=True)
class Participant(GS):
    name:TextLike
    user_name:TextLike
    mention:TextLike
    pronouns_set:Pronoun_Set = COMMON_PRONOUNS[0]
    @override
    def __str__(self) -> TextLike:
        return self.user_name
