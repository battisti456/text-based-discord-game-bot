import logging
from typing import Callable, Iterable, Mapping, Optional, override

from config.config import config
from utils.types import (
    KickReason,
    Number,
    Placement,
    PlayerDict,
    PlayerId,
    PlayerMapOptional,
    PlayerPlacement,
)

class Color_Filter(logging.Filter):
    start_grey = "\x1b[38;20m"
    start_yellow = "\x1b[33;20m"
    start_red = "\x1b[31;20m"
    start_bold_red = "\x1b[31;1m"
    color = {
        logging.INFO : start_grey,
        logging.WARNING : start_yellow,
        logging.ERROR : start_red,
        logging.CRITICAL : start_bold_red
    }
    color_end = "\x1b[0m"
    @override
    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        record.start_color = Color_Filter.color[record.levelno]
        record.end_color = Color_Filter.color_end
        return record

fmt = logging.Formatter('%(start_color)s%(asctime)s::%(levelname)s%(end_color)s::%(name)s::%(message)s')
flt = Color_Filter()
h1 = logging.StreamHandler()
h1.setLevel(config['logging_level'])
h1.setFormatter(fmt)
def get_logger(name:str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.addFilter(flt)
    logger.addHandler(h1)
    logger.setLevel(config['logging_level'])
    return logger

#player/players being _______
kick_text:dict[KickReason,str] = {
    'timeout': 'removed for exceeding the timeout',
    'eliminated': 'eliminated from the game',
    'unspecified': 'kicked for unspecified reasons'
}

def treat_responses[T](responses:PlayerMapOptional[T],players:Optional[None]=None) -> PlayerDict[T]:
        new_responses:PlayerDict[T] = {}
        for player in responses:
            if players is not None:
                if player not in players:
                    continue
            value:T|None = responses[player]
            if value is not None:
                new_responses[player] = value
        return new_responses

def make_player_dict[T](
        players:Iterable[PlayerId],
        value:T|Callable[[],T]|Callable[[PlayerId],T] = None
        ) -> PlayerDict[T]:
    to_return:PlayerDict[T] = {}
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

def score_to_placement[Participant](
        score:Mapping[Participant,Number], 
        all_participants:Optional[Iterable[Participant]] = None,
        reverse:bool = False
        ) -> Placement[Participant]:
    """
    creates a player placement with lowest scores placing higher
    
    reverse reverses this order
    """
    _score:dict[Number,set[Participant]] = {}
    for participant,point in score.items():
        if point not in _score:
            _score[point] = set()
        _score[point].add(participant)
    points = list(_score)
    points.sort(reverse=reverse)
    to_return:list[tuple[Participant,...]] = list(
        tuple(_score[point]) for point in points
    )

    if all_participants is not None and set(all_participants) != set(score):
        to_return.append(tuple(set(all_participants)-set(score)))
    return tuple(to_return)
def _merge_placements(pl1:PlayerPlacement,pl2:PlayerPlacement):
    i:int = 0
    while i < len(pl1):
        if len(pl1[i]) > 1:
            seperated:list[list[PlayerId]] = []
            for group in pl2:
                new = list(player for player in pl1[i] if player in group)
                if new:#if there were any relevant players in that group
                    seperated.append(new)
            pl1 = (
                pl1[0:i] + 
                tuple(
                    tuple(player for player in pl1[i] if player in group) 
                    for group in pl2 
                    if any(player in group for player in pl1[i])) + 
                pl1[i+1:-1])
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
