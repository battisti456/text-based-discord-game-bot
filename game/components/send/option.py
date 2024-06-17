from typing import override, Optional


class Option(object):
    """a basic object storing the text and the emoji representations of a bullet point item"""
    def __init__(self,text:Optional[str] = None, emoji:Optional[str] = None):
        self.text = text
        self.emoji = emoji
    @override
    def __str__(self):
        return f"{self.emoji} (*{self.text}*)"