from typing import TypeVar

R = TypeVar('R')
def L(lst:list[R|None]|list[None]|list[R]|None) -> list[R]:
    """
    corrects a list or None output to only be a list of items that are not None;
    returns [] when None is inputted
    """
    if lst is None:
        return []
    else:
        return list(item for item in lst if not item is None)