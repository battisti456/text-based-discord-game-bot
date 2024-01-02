from typing import TypeVar
from typing import Hashable, Iterable, Optional, Callable, Mapping, Dict

DataType = TypeVar('DataType')

type PlayerId = Hashable
type MessageId = Hashable
type ChannelId = Hashable
type InteractionId = Hashable
type PlayerPlacement = list[list[PlayerId]]

type PlayerDictOptional[DataType] = dict[PlayerId,Optional[DataType]]
type PlayerDict[DataType] = dict[PlayerId,DataType]

def make_player_dict(players:Iterable[PlayerId],value:DataType|Callable[[],DataType] = None) -> PlayerDict[DataType]:
    to_return:PlayerDict[DataType] = {}
    for player in players:
        if callable(value):
            to_return[player] = value()
        else:
            to_return[player] = value
    return to_return

def correct_int(value:int|None) -> int:
    if value is None:
        return 0
    else:
        return value
def correct_str(value:str|None) -> str:
    if value is None:
        return ""
    else:
        return value