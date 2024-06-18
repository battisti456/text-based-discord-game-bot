from typing import override
from dataclasses import dataclass
@dataclass(frozen=True)
class Option(object):
    """a basic object storing the text and the emoji representations of a bullet point item"""
    text:str
    emoji:str
    long_text:str
    @override
    def __str__(self):
        return f"{self.emoji} (*{self.text}*)"