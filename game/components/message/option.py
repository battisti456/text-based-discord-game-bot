import dataclasses
from typing import Mapping, Sequence,Optional, overload

from utils.emoji_groups import NO_YES_EMOJI, COLORED_CIRCLE_EMOJI

@dataclasses.dataclass(frozen = True)
class Option():
    text_part:str
    emoji_part:str

@overload
def make_options(
        arg1:Mapping[str,str],
        arg2:Sequence[str]|None = ...) -> set[Option]:
    ...
@overload
def make_options(
        arg1:Sequence[str],
        arg2:Sequence[str]|None = ...) -> set[Option]:
    ...
def make_options(
        arg1:Mapping[str,str]|Sequence[str],
        arg2:Optional[Sequence[str]] = None) -> set[Option]:
    """Generates a set of options from the given arguments. Either a single mapping of text to emoji, or a list of text and a list of emoji.

    Args:
        arg1: A sequence of text or a mapping of text to emoji, if mapping arg2 is ignored
        arg2: A sequence of emoji, if None defaults to COLORED_CIRCLE_EMOJI

    Returns:
        Set of options.
    """
    if isinstance(arg1,Mapping):
        return set(
            Option(text,emoji) for text, emoji in arg1.items()
        )
    elif arg2 is not None:
        return set(
            Option(text,arg2[i]) for i, text in enumerate(arg1)
        )
    else:
        return make_options(arg1,COLORED_CIRCLE_EMOJI)

no_yes_options = make_options(("no","yes"),NO_YES_EMOJI)
