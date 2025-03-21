from typing import TypedDict, Unpack, TYPE_CHECKING
import inspect
import dataclasses

from game.components.send.sendable.sendable import Sendable, SENDABLES, PROTOTYPE_SENDABLES

if TYPE_CHECKING:
    from smart_text import TextLike
    from game.components.send import Option, Address

class MakeSendableArgs(TypedDict, total = False):
    text:'TextLike'
    attach_files:tuple[str,...]
    with_options:tuple['Option',...]
    min_selectable:int
    max_selectable:int
    hint_text:'TextLike'
    reference_message:'Address'

def args_satisfied(prototype:type[Sendable],kwargs:MakeSendableArgs) -> bool:
    sig = inspect.signature(prototype)
    return all(
        arg_name in kwargs for arg_name,v in sig.parameters.items()
        if v.default is inspect._empty)

def make_sendable(
        **kwargs:Unpack[MakeSendableArgs]
) -> Sendable:
    for sendable in SENDABLES:
        try:
            return sendable(**kwargs)#type:ignore
        except TypeError:
            ...
    prototypes = set(
        prototype for prototype in PROTOTYPE_SENDABLES
        if args_satisfied(prototype,kwargs)
    )
    @dataclasses.dataclass(frozen=True)
    class Made_Sendable(*prototypes):
        ...
    return Made_Sendable(**kwargs)
