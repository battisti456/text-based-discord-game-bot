import random
from typing import Iterable, Mapping, Optional, Any

from utils.types import Grouping, GroupingSafeVar


def get_first[T](grouping:Iterable[T]) -> T:
    for item in grouping:
        return item
    raise IndexError(f"Empty grouping {grouping}, cannot get first.")

def arg_fix_grouping(default:Grouping[GroupingSafeVar],inpt:Optional[GroupingSafeVar|Grouping[GroupingSafeVar]]) -> tuple[GroupingSafeVar,...]:
    if inpt is None:
        return tuple(default)
    elif isinstance(inpt,Grouping):
        return tuple(inpt)
    else:
        return (inpt,)
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
        return list(item for item in lst if item is not None)
def linear_conversion(val:float,start_range:tuple[float,float],end_range:tuple[float,float]) -> float:
    return (val-start_range[0])/(start_range[1]-start_range[0])*(end_range[1]-end_range[0])+end_range[0]
def random_in_range(start:float,end:float) -> float:
    return linear_conversion(
        random.random(),
        (0,1),
        (start,end)
    )
def random_from(obj:Any,num:int = 0) -> float:
    r = random.Random(id(obj))
    i = 0
    while i < num:
        r.random()
        i += 1
    return r.random()
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