from typing import Iterable, Any

def wordify_iterable(values:Iterable[str|Any],operator:str = 'and',comma:str = ",") -> str:
    #returns a string comma comma anding an iterator of strings
    to_return = ""
    if not isinstance(values,list):
        values = list(values)
    if len(values) == 0:
        return ""
    elif len(values) == 1:
        return values[0]
    elif len(values) == 2:
        return f"{values[0]} {operator} {values[1]}"
    for i in range(len(values)):
        if i != 0:
            if i == len(values) -1:#is last
                to_return += f"{comma} {operator} "
            else:
                to_return += f"{comma} "
        if isinstance(values[i],str):
            to_return += values[i]
        else:
            to_return += str(values[i])
    return to_return