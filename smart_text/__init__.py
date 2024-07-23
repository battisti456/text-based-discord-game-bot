from typing import Iterable

class Smart_Text(str):
    ...

def join(values:Iterable,join:'TextLike' = '') -> 'TextLike':
    cumulative:'TextLike' = ""
    first = True
    for value in values:
        if not first:
            cumulative += join
        first = False
        cumulative += value
    return cumulative

TextLike = str|Smart_Text