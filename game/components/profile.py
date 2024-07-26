from typing import TYPE_CHECKING, Any

from typeguard import TypeCheckError, check_type

from utils.logging import get_logger
from utils.types import TypeHint

logger = get_logger(__name__)

if TYPE_CHECKING:
    from game.game import Game
    from game.components.game_config import ConfigHint, Game_Config

class LookUpError(Exception):
    ...

class Profile():
    def __init__(self):
        self.settings:dict[str,Any] = {}
    def look_up_game_setting(self,cls:type['Game'],attr:str,hint:ConfigHint) -> Any:
        tpe:TypeHint = Any
        item:'Game_Config.Item|None' = None
        if len(hint) == 1:
            tpe = hint[0]
        elif len(hint) == 2:
            tpe,item = hint

        for base in cls.__mro__:
            if not issubclass(base,Game) or base == Game:
                continue
            name = f"game.{base.__name__}.{attr}".lower()
            if name not in self.settings.keys():
                continue
            value = self.settings[name]
            try:
                check_type(value,tpe)
            except TypeCheckError:
                logger.error(f"{self} has setting '{name} = {value}', but this does not meet the type requirement of '{type}'.")
                continue
            if item is not None:
                if not item.check(value):
                    logger.error(f"{self} has setting '{name} = {value}', but this fails the failsafe check." + (
                        '' if item.description is None else f"This item is described with '{item.description}'."
                    ))
                    continue
            return value
        raise LookUpError()

from game.game import Game  # noqa: E402
