from dataclasses import dataclass
from typing import override, Iterable

from smart_text import TextLike
from utils.grammar.pronoun_set import COMMON_PRONOUNS, Pronoun_Set
from utils.grammar import wordify_iterable
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

def name_participants(participants:Iterable[Participant],operator:TextLike = 'and',comma:TextLike = ',') -> TextLike:
    return wordify_iterable(
        (participant.name for participant in participants),
        operator,
        comma
    )
def user_name_participants(participants:Iterable[Participant],operator:TextLike = 'and',comma:TextLike = ',') -> TextLike:
    return wordify_iterable(
        (participant.user_name for participant in participants),
        operator,
        comma
    )
def mention_participants(participants:Iterable[Participant],operator:TextLike = 'and',comma:TextLike = ',') -> TextLike:
    return wordify_iterable(
        (participant.mention for participant in participants),
        operator,
        comma
    )