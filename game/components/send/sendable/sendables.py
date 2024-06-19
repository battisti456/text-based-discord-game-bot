from dataclasses import dataclass

from game.components.send.sendable.prototype_sendables import Text, Attach_Files, With_Options, With_Text_Field


@dataclass(frozen=True)
class Text_Only(Text):
    ...

@dataclass(frozen=True)
class Text_With_Options(Text,With_Options):
    ...

@dataclass(frozen=True)
class Text_With_Text_Field(Text,With_Text_Field):
    ...

@dataclass(frozen=True)
class Attach_Files_Only(Attach_Files):
    ...

@dataclass(frozen=True)
class Text_With_Files(Text,Attach_Files):
    ...

@dataclass(frozen = True)
class Text_With_Options_And_Text_Field(Text,With_Options,With_Text_Field):
    ...