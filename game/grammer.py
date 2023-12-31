from typing import Iterable, Any
import uuid

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
def ordinate(num:int|str) -> str:
    #takes a number and returns a string of the digits with the correct 'st','nd','rd' of 'th' ending for the ordinal
    num = str(num)
    ordinal = ""
    if num[-1] == '1':
        ordinal = "st"
    elif num[-1] == '2':
        ordinal = "nd"
    elif num[-1] == '3':
        ordinal = "rd"
    else:
        ordinal = "th"
    if num in (11,12,13):
        ordinal = 'th'
    return num + ordinal
TEMP_PATH = "temp"

def temp_file_path(type:str) -> str:
    #returns a (probably) unique file name in the temp folder
    return f"{TEMP_PATH}//{uuid.uuid4()}{type}"