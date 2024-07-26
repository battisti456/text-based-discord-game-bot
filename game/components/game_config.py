from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    Optional,
    dataclass_transform,
    get_args,
    get_origin,
    override,
)

from game.components.profile import LookUpError
from game.game import Game
from utils.types import TypeHint

if TYPE_CHECKING:
    from game.game import Game


type ConfigHint = tuple[()]|tuple[TypeHint]|tuple[TypeHint,'Game_Config.Item']

@dataclass_transform()
class Game_Config():
    @dataclass(frozen = True)
    class Item():
        description:Optional[str] = None
        check_func:Optional[Callable[[Any],bool]] = None
        def check(self,value:Any) -> bool:
            if self.check_func is None:
                return True
            return self.check_func(value)
    def __init__(self,game:'Game'):
        self._game: 'Game' = game
    def get_hints(self,name:str) -> ConfigHint:
        if name not in self.__class__.__annotations__:
            return tuple(())
        type_hint:TypeHint = self.__class__.__annotations__[name]
        if get_origin(type_hint) is Annotated:
            args:tuple[TypeHint,Game_Config.Item] = get_args(type_hint)
            if len(args) == 2 and isinstance(args[1],Game_Config.Item):
                return args
            else:
                return (args[0],)
        else:
            return (type_hint,)
        
    @override
    def __getattribute__(self, name: str):
        if name == '_game':
            return super().__getattribute__(name)
        try:
            return self._game.profile.look_up_game_setting(self._game.__class__,name,self.get_hints(name))
        except LookUpError:
            return super().__getattribute__(name)