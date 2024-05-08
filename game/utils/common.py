#from typing import TypeVar

#R = TypeVar('R')
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