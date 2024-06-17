from dataclasses import dataclass, field

SENDABLES:list[type['Sendable']] = []

@dataclass(frozen=True)
class Sendable():
    is_prototype:bool = field(init=False,repr=False,hash=False,compare=False,kw_only=True)
    def __init_subclass__(cls, is_prototype = False) -> None:
        if not all(c.is_prototype for c in cls.__bases__ if issubclass(c,Sendable)):
            raise ValueError(f"{cls}'s bases {cls.__bases__} contains non prototypes")
        cls.is_prototype = is_prototype
        if not is_prototype:
            SENDABLES.append(cls)
