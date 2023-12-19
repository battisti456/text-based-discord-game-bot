import game_handler
from time import sleep
from typing import Callable, Iterable, TypeVar, ParamSpec, NewType, Any
import functools


userid = NewType("userid",int)
messageid = NewType("messageid",int)
channelid = NewType("channelid",int)

P = ParamSpec('P')
R = TypeVar('R')


GH = game_handler.Game_Handler
CHECK_TIME = 0.1
      
def police_messaging(func:Callable[P,R]) -> Callable[P,R]:
    #Adds the class the function was first defined in to current_class_execution, only to be used on asynchronous game.Game methods
    @functools.wraps(func)
    async def wrapped(*args:P.args,**kwargs:P.kwargs) -> R:
        classes:list = list(args[0].__class__.__bases__)
        classes.append(type(args[0].__class__))
        #classes.reverse()
        for clss in classes:
            if hasattr(clss,func.__name__):
                c = clss
                break
        stored = args[0].current_class_execution
        args[0].current_class_execution = c
        to_return = await func(*args,**kwargs)
        args[0].current_class_execution = stored
        return to_return
    return wrapped

def wordify_iterable(values:Iterable[str],operator:str = 'and',comma:str = ",") -> str:
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
def link_to(values:Iterable[Any],link_to = None,d:dict = dict()) -> dict:
    #returns a dict linking values to link_to
    for value in values:
        d[value] = link_to
    return d

def one_depth_len(lst:list[R|list[R]]) -> int:
    #returns number of items in a list of items and lists of items
    to_return = 0
    for item in lst:
        try:
            to_return += len(item)
        except TypeError:
            to_return += 1
    return to_return
def one_depth_flat(lst:list[R|list[R]]) -> list[R]:
    #flattens a list of lists and non-lists into one list
    to_return:list[R] = []
    for item in lst:
        try:
            to_return += item
        except TypeError:
            to_return.append(item)
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
    
from game.game import Game as Game