from typing import TypeVar
from typing import Hashable, Iterable, Optional, Callable, Mapping, Dict, Awaitable, Literal

DataType = TypeVar('DataType')
R = TypeVar('R')

type PlayerId = Hashable
type MessageId = Hashable
type ChannelId = Hashable
type InteractionId = Hashable
type PlayerPlacement = list[list[PlayerId]]

type PlayerDictOptional[DataType] = dict[PlayerId,Optional[DataType]]
type PlayerDict[DataType] = dict[PlayerId,DataType]

type KickFunc = Callable[[list[PlayerId]],Awaitable[bool]]
type KickReason = Literal['timeout','eliminated','unspecified']

#player/players being _______
kick_text:dict[KickReason,str] = {
    'timeout': 'removed due to exceeding the timeout',
    'eliminated': 'eliminated from the game',
    'unspecified': 'kicked for unspecified reasons'
}

class GameBotException(Exception):
    ...
class GameException(GameBotException):
    ...
class GameEndException(GameException):
    def __init__(self,message:Optional[str] = None):
        """
        message: ...caused by ________.
        """
        if message is not None:
            super().__init__(message)
        else:
            super().__init__()
        self._explanation:str = "an unspecified reason" 
    @property
    def explanation(self) -> str:
        start:str = "The game has ended due to "
        end:str = "."
        if self.args:
            end = f"caused by {self.args[0]}."
        return f"{start}{self._explanation}{end}"
    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.explanation}"

class GameEndInsufficientPlayers(GameEndException):
    def __init__(self,message:Optional[str] = None):
        """
        message: ...caused by ________.
        """
        GameEndException.__init__(self,message)
        self._explanation:str = "a lack of sufficient remaining players" 

def treat_responses(self,responses:PlayerDictOptional[R],players:Optional[None]=None) -> PlayerDict[R]:
        new_responses:PlayerDict[R] = {}
        for player in responses:
            if not players is None:
                if not player in players:
                    continue
            value:R|None = responses[player]
            if not value is None:
                new_responses[player] = value
        return new_responses

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