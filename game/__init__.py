import game_handler
from time import sleep
from typing import Callable, Iterable, TypeVar, ParamSpec, NewType, Any, Awaitable, TypedDict, Hashable
import functools


PlayerId = Any
MessageId = Any
ChannelId = Any
InteractionId = Any

P = ParamSpec('P')
R = TypeVar('R')


GH = game_handler.Game_Handler
CHECK_TIME = 0.1

class IsDone(object):
    def __init__(self,value = False):
        self.value = False
    def set_done(self,value = True):
        self.value = value
    def __bool__(self):
        return self.value
class MessageDict(TypedDict):
    message:str
    message_id:MessageId
    channel_id:ChannelId
    files:list[str]

    
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

def sub_sync_lock_maker(
        master_sync_lock:Callable[[bool],Awaitable[bool]],all_done:IsDone,
        responses:dict[PlayerId,Any],users:list[PlayerId]) -> Callable[[bool],Awaitable[bool]]:
    async def sub_sync_lock(is_done:bool) -> bool:
        if master_sync_lock is None:
            if all_done:
                return True
            else:
                all_done.set_done(all(not responses[user] is None for user in users))
                return all_done
        else:
            all_done.set_done(all(not responses[user] is None for user in users))
            return await master_sync_lock(all_done)
    return sub_sync_lock

def userid_to_string(user_id:PlayerId):
    if isinstance(user_id,int):
        return f"<@{user_id}>"
    else:#it is an iterable
        return wordify_iterable(userid_to_string(uid) for uid in user_id)
def make_message_dict(*args,**kwargs:MessageDict) -> MessageDict:
    to_return:MessageDict = {}
    for arg in args:
        if isinstance(arg,str):
            if "message" not in to_return:
                to_return["message"] = arg
            else:
                raise Exception("Too many strings assigned in make_message_dict")
        elif isinstance(arg,int):
            if not "channel_id" in to_return:
                to_return["channel_id"] = arg
            elif not "message_id" in to_return:
                to_return["message_id"] = arg
            else:
                raise Exception("Too many intigers assigned in make_message_dict")
        elif isinstance(arg,list):
            if not "files" in to_return:
                to_return["files"] = arg
            else:
                raise Exception("Too many lists assigned in make_message_dict")
    for kwarg in kwargs:
        if not kwarg in to_return:
            to_return[kwarg] = kwargs[kwarg]
        else:
            raise Exception(f"Tried to assign '{kwarg}' when it was already defined in make_message_dict")
    if not "message" in to_return:
        to_return["message"] = ""
    if not "message_id" in to_return:
        to_return["message_id"] = None
    if not "channel_id" in to_return:
        to_return["channel_id"] = None
    if not "files" in to_return:
        to_return["files"] = []
    return to_return
        

from game.game import Game as Game