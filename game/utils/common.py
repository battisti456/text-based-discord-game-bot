#from typing import TypeVar

#R = TypeVar('R')

from typing import Mapping, Iterable


type Number = int|float

from typing import Optional
def arg_fix_iterable[R](default:Iterable[R],inpt:Optional[R|Iterable[R]]) -> tuple[R,...]:
    if inpt is None:
        return tuple(default)
    elif isinstance(inpt,Iterable):
        return tuple(inpt)
    else:
        return (inpt,)
def arg_fix_frozenset[R](default:frozenset[R],inpt:Optional[R|frozenset[R]]) -> frozenset[R]:
    if inpt is None:
        return default
    elif isinstance(inpt,frozenset):
        return inpt
    else:
        return frozenset([inpt])
def arg_fix_tuple[R](default:tuple[R,...],inpt:Optional[R|tuple[R,...]]) -> tuple[R,...]:
    if inpt is None:
        return default
    elif isinstance(inpt,tuple):
        return inpt
    else:
        return (inpt,)
def arg_fix_list[R](default:list[R],inpt:Optional[R|list[R]]) -> list[R]:
    if inpt is None:
        return default
    elif isinstance(inpt,list):
        return inpt
    else:
        return [inpt]
def arg_fix_dict[K,R](relevant_keys:Iterable[K],default_amount:R,inpt:Optional[R|dict[K,R]]) -> dict[K,R]:
    if inpt is None:
        return {key:default_amount for key in relevant_keys}
    elif isinstance(inpt,dict):
        return inpt
    else:
        return {key:inpt for key in relevant_keys}
def arg_fix_map[K,R](relevant_keys:Iterable[K],default_amount:R,inpt:Optional[R|Mapping[K,R]]) -> Mapping[K,R]:
    if inpt is None:
        return {key:default_amount for key in relevant_keys}
    elif isinstance(inpt,Mapping):
        return inpt
    else:
        return {key:inpt for key in relevant_keys}

def L[R](lst:list[R|None]|list[None]|list[R]|None) -> list[R]:
    """
    corrects a list or None output to only be a list of items that are not None;
    returns [] when None is inputted
    """
    if lst is None:
        return []
    else:
        return list(item for item in lst if not item is None)


"""
def _list_combine(current:list[R],future_options:list[Sequence[R]]) -> list[list[R]]:
    if len(future_options) == 0:
        return [current]
    to_return:list[list[R]] = []
    for option in future_options[0]:
        to_return += _list_combine(current + [option],future_options[1:])
    return to_return
def list_combine(options:list[Sequence[R]]) -> list[list[R]]:
    \"""
    returns a list of combinations of type R\"""
    return _list_combine([],options)
"""