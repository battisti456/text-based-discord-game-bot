from typing import TypeVar
from typing import Hashable, Iterable, Optional, Callable, Mapping, Dict, Awaitable, Literal
from numbers import Real


DataType = TypeVar('DataType')
R = TypeVar('R')

type PlayerId = Hashable
type MessageId = Hashable
type ChannelId = Hashable
type InteractionId = Hashable
type PlayerPlacement = list[list[PlayerId]]

type PlayerDictOptional[DataType] = dict[PlayerId,Optional[DataType]]
type PlayerDict[DataType] = dict[PlayerId,DataType]

type KickReason = Literal['timeout','eliminated','unspecified']

type Operators = Literal['command','run_game']

#player/players being _______
kick_text:dict[KickReason,str] = {
    'timeout': 'removed for exceeding the timeout',
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
            end = f" caused by {self.args[0]}."
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

def make_player_dict(
        players:Iterable[PlayerId],
        value:DataType|Callable[[],DataType]|Callable[[PlayerId],DataType] = None
        ) -> PlayerDict[DataType]:
    to_return:PlayerDict[DataType] = {}
    for player in players:
        if callable(value):
            try:
                to_return[player] = value(player) # type: ignore
            except TypeError:
                to_return[player] = value() # type: ignore
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
    
def score_to_placement(score:PlayerDict[float]|PlayerDict[int], all_players:Optional[list[PlayerId]] = None,reverse:bool = False) -> PlayerPlacement:
    """
    creates a player placement with lowest scores placing higher
    
    reverse reverses this order
    """
    players = list(score)
    players.sort(key=lambda player: score[player],reverse=reverse)
    to_return:PlayerPlacement = []
    for i in range(len(players)):
        if i:
            if score[players[i]] == score[to_return[i-1][0]]:
                to_return[i-1].append(players[i])
                continue
        to_return.append([players[i]])
    if not all_players is None and set(all_players) != set(players):
        to_return.append(list(set(all_players)-set(players)))
    return to_return
def _merge_placements(pl1:PlayerPlacement,pl2:PlayerPlacement):
    i:int = 0
    while i < len(pl1):
        if len(pl1[i]) > 1:
            seperated:PlayerPlacement = []
            for group in pl2:
                new = list(player for player in pl1[i] if player in group)
                if new:#if there were any relevant players in that group
                    seperated.append(new)
            pl1 = pl1[0:i] + seperated + pl1[i+1:-1]
            i += len(seperated)
        else:
            i += 1
    return pl1
def merge_placements(*args:PlayerPlacement)-> PlayerPlacement:
    """
    merges placements with highes priority placements being eralier in the order
    """

    #add code to deal with players not being in all placements
    to_return:PlayerPlacement = args[0]
    for pl in args[1:]:
        to_return = _merge_placements(to_return,pl)
    return to_return
