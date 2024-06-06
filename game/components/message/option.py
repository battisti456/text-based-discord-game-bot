import dataclasses
from typing import Mapping, Sequence,Optional, overload

@dataclasses.dataclass(frozen = True)
class Option():
    text_part:str
    emoji_part:str

@overload
def make_options(
        arg1:Mapping[str,str],
        arg2:None = ...) -> set[Option]:
    ...
@overload
def make_options(
        arg1:Sequence[str],
        arg2:Sequence[str] = ...) -> set[Option]:
    ...
def make_options(
        arg1:Mapping[str,str]|Sequence[str],
        arg2:Optional[Sequence[str]] = None) -> set[Option]:
    """Generates a set of options from the given arguments. Either a single mapping of text to emoji, or a list of text and a list of emoji.

    Args:
        arg1: Either a mapping from text to emoji, or a sequence of text.
        arg2: A sequence of emoji, unless a mapping was set as arg1, then it is None

    Raises:
        Exception: If arg2 is None while arg1 is a sequence

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
        raise Exception("Incorrect argument format for make options!")
