from typing import override, Sequence, Optional
from dataclasses import dataclass

import utils.emoji_groups

@dataclass(frozen=True)
class Option(object):
    """a basic object storing the text and the emoji representations of a bullet point item"""
    text:str
    emoji:str
    long_text:str
    @override
    def __str__(self):
        return f"{self.emoji} (*{self.text}*)"

def make_options(labels:Sequence[str],emojis:Optional[Sequence[str]] = None,long_labels:Optional[Sequence[str]] = None) -> tuple[Option,...]:
    if emojis is None:
        emojis = utils.emoji_groups.COLORED_CIRCLE_EMOJI
    if long_labels is None:
        long_labels = labels
    return tuple(Option(labels[i],emojis[i],long_labels[i]) for i in range(len(labels)))

NO_YES_OPTIONS = make_options(('no','yes'),utils.emoji_groups.NO_YES_EMOJI)