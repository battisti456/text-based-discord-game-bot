from dataclasses import dataclass

from smart_text import TextLike, join

from typing import Optional, Iterator

from utils.grammar import append_s

DEFAULT_PRONOUN_STRING_LENGTH = 3

@dataclass(frozen=True)
class Pronoun_Set():
    "Names of pronoun conjugations sourced from https://uwm.edu/lgbtrc/support/gender-pronouns/."
    subject:TextLike
    "___ laughed at the notion of a gender binary."
    object:TextLike
    "They tried to convince ___ that asexuality does not exist."
    possessive:TextLike
    "___ favorite color is unknown."
    possessive_pronoun:TextLike
    "The pronoun card is ___."
    reflexive:TextLike
    "_subject_ think(s) highly of ___."
    plural_form:bool
    "whether verbs need to be conjugated as if this were a plural pronoun"
    def values(self) -> Iterator[TextLike]:
        yield self.subject
        yield self.object
        yield self.possessive
        yield self.possessive_pronoun
        yield self.reflexive
    def to_string(self) -> TextLike:
        to_add:list[TextLike] = []
        for value in self.values():
            if value not in to_add:
                to_add.append(value)
        to_add = to_add[:DEFAULT_PRONOUN_STRING_LENGTH]
        return join(to_add,'/')
    @classmethod
    def new(
        cls,
        subject:TextLike,
        object:Optional[TextLike] = None,
        possessive:Optional[TextLike] = None,
        possessive_pronoun:Optional[TextLike] = None,
        reflexive:Optional[TextLike] = None,
        plural_form:bool = False) -> 'Pronoun_Set':
        object = subject if object is None else object
        possessive = possessive if possessive is not None else object
        return cls(
            subject=subject,
            object=object,
            possessive=possessive,
            possessive_pronoun=possessive_pronoun if possessive_pronoun is not None else append_s(possessive),
            reflexive=reflexive if reflexive is not None else append_s(object),
            plural_form = plural_form
        )

COMMON_PRONOUNS:tuple[Pronoun_Set,...] = (
    Pronoun_Set.new(
        subject='they',
        object='them',
        possessive='their',
        plural_form=True
    ),
    Pronoun_Set.new(
        subject='she',
        object='her',
    ),
    Pronoun_Set.new(
        subject='he',
        object='him',
        possessive='his'
    ),
    Pronoun_Set.new(
        subject='ze',
        object='hir',
    ),
    Pronoun_Set.new(
        subject='zie',
        object='hir',
    ),
    Pronoun_Set.new(
        subject='xe',
        object='xem',
        possessive='xyr'
    ),
    Pronoun_Set.new(
        subject='ve',
        object='ver',
        possessive='vis'
    ),
    Pronoun_Set.new(
        subject='per',
        possessive='pers'
    ),
    Pronoun_Set.new(
        subject='e',
        object='em',
        possessive='eir',
        reflexive='eirself'
    ),
    Pronoun_Set.new(
        subject='ey',
        object='em',
        possessive='eir',
        reflexive='eirself'
    ),
    Pronoun_Set.new(
        subject='ae',
        object='aer',
    ),
    Pronoun_Set.new(
        subject='fae',
        object='faer',
    ),
    Pronoun_Set.new(
        subject='it',
        possessive='its'
    )
)
