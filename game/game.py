import functools
from typing import Awaitable, Callable, Optional, ParamSpec, TypeVar, overload, override, Any

import utils.emoji_groups
from game import kick_text, score_to_placement
from game.components.game_interface import Game_Interface
from game.components.input_ import Input
from game.components.input_.response_validator import (
    ResponseValidator,
    default_text_validator,
    not_none,
)
from game.components.interface_component import Interface_Component
from game.components.participant import (
    Player,
    PlayerDict,
    PlayerDictOptional,
    PlayerMapOptional,
    PlayerPlacement,
    Players,
    mention_participants
)
from utils.common import arg_fix_grouping
from utils.exceptions import GameEndException, GameEndInsufficientPlayers
from utils.grammar import ordinate, wordify_iterable
from utils.logging import get_logger
from utils.types import (
    Grouping,
    KickReason,
)
from game.components.send.interaction import Send_Text, Select_Options
from game.components.send import Address

logger = get_logger(__name__)

MULTIPLE_CHOICE_LINE_THRESHOLD = 30

R = TypeVar('R')
P = ParamSpec('P')

class Game(Interface_Component):
    """
    the base objects all games are built upon
    """
    def __init__(self,gi:Game_Interface):
        if not hasattr(self,'initialized_bases'):#prevents double initialization, although it probably wouldn't hurt anyway
            super().__init__(gi)
            self.initialized_bases:list[type[Game]] = [Game]
            self.current_class_execution:Optional[type[Game]] = None
            self.classes_banned_from_speaking:list[type[Game]] = []

            self.kicked:PlayerDict[tuple[int,KickReason]] = {}
            self.game_end_exception:Optional[GameEndException] = None
    def is_player_kicked(self,player:Player) -> bool:
        return player in self.kicked
    @property
    def kicked_players(self) -> tuple[Player,...]:
        return tuple(player for player in self.all_players if self.is_player_kicked(player))#maintian order
    @property 
    def unkicked_players(self) -> tuple[Player,...]:
        return tuple(player for player in self.all_players if not self.is_player_kicked(player))
    async def game_intro(self):
        ...
    async def game_setup(self):
        ...
    async def game_outro(self):
        ...
    async def game_unsetup(self):
        ...
    async def _run(self):
        """
        the actual running of the game, meant to be overloaded
        """
        return []
    async def run(self):
        """
        intended function to run the selected game
        """
        logger.info(f"Setting up {self}.")
        await self.game_setup()
        logger.info(f"Playing intro of {self}.")
        await self.game_intro()
        try:
            logger.info(f"Starting to run {self}.")
            await self._run()
            logger.info(f"Gracefully finished running {self}.")
        except GameEndException as e:
            logger.warning(f"{self} ended due to {e}.")
            self.game_end_exception = e
            await self.say(e.explanation)
        except:  # noqa: E722
            logger.exception("Game failed due to unexpected error.")
            await self.say("The game has experienced an unforseen exception and will attempt to close itself...")
        logger.info(f"Un-setting up {self}.")
        await self.game_unsetup()
        logger.info(f"Playing outro for {self}.")
        await self.game_outro()
        logger.info(f"Done running {self}.")
    def generate_placements(self) -> PlayerPlacement:
        return tuple()
    def generate_kicked_placements(self) -> PlayerPlacement:
        return (self.unkicked_players,) + score_to_placement({player:self.kicked[player][0] for player in self.kicked},reverse=True)
    #region basic_inputs
    #region basic_multiple_choice overloads
    @overload
    async def basic_multiple_choice(
            self,
            content:Optional[str|Address]=...,
            options:list[str]=...,
            who_chooses:Optional[Players]=...,
            emojis:Optional[list[str]]=..., 
            allow_answer_change:bool=...,
            response_validator:ResponseValidator[Select_Options,Player] = ...) -> PlayerDict[int]:
        ...
    @overload
    async def basic_multiple_choice(
            self,
            content:Optional[str|Address]=...,
            options:list[str]=...,
            who_chooses:Player=...,
            emojis:Optional[list[str]]=...,
            allow_answer_change:bool=...,
            response_validator:ResponseValidator[Select_Options,Player] = ...) -> int:
        ...
    #endregion
    async def basic_multiple_choice(
            self,
            content:Optional[str|Address] = None,
            options:list[str] = [],
            who_chooses:Optional[Players|Player] = None,
            emojis:Optional[list[str]] = None,
            allow_answer_change:bool = True,
            response_validator:ResponseValidator[Select_Options,Player] = not_none) -> PlayerDict[int]|int:
        """
        sets up and runs a multiple choice input, returning its responses
        
        content: text to send in a message that will be replied to
        
        options: the list of names of options that the players choose between
        
        who_chooses: the list of players whose input matters, if None assumes self.players
        
        emoji: the list of emoji symbols representing the choices, if None, defaults to colored circles
        
        channel_id: what channel_id this message should be sent on

        allow_answer_change: weather or not users are permitted to change their response while the input is running
        """
        w = arg_fix_grouping(self.unkicked_players,who_chooses)
        responses:PlayerDictOptional = await self._basic_multiple_choice(
            content=content,
            options=options,
            who_chooses=w,
            emojis=emojis,
            allow_answer_change=allow_answer_change,
            response_validator=response_validator

        )
        await self.kick_none_response(responses)
        clean_responses = self.clean_player_dict(responses,w,frozenset(self.unkicked_players))
        if isinstance(who_chooses,Grouping) or who_chooses is None:
            return clean_responses
        else:
            if tuple(w)[0] in clean_responses:
                return clean_responses[tuple(w)[0]]
            else:
                return -1#The player did not respond and got kicked, function must still return though
    #region basic_no_yes overloads
    @overload
    async def basic_no_yes(
            self,
            content:Optional[str|Address]=...,
            who_chooses:Optional[Grouping[Player]]=...,
            allow_answer_change:bool=...,
            response_validator:ResponseValidator[Select_Options,Player] = ...) -> PlayerDict[int]:
        ...
    @overload
    async def basic_no_yes(
            self,
            content:Optional[str|Address]=...,
            who_chooses:Player=...,
            allow_answer_change:bool=...,
            response_validator:ResponseValidator[Select_Options,Player] = ...) -> int:
        ...
    #endregion
    async def basic_no_yes(
            self,
            content:Optional[str|Address] = None,
            who_chooses:Optional[Player|Grouping[Player]] = None,
            allow_answer_change:bool = True,
            response_validator:ResponseValidator[Select_Options,Player] = not_none) -> int | PlayerDict[int]:
        """
        runs self.basic_multiple_choice with ('no','yes') as the options
        
        content: text to send in a message that will be replied to
        
        who_chooses: the list of players whose input matters, if None assumes self.players
        
        channel_id: what channel_id this message should be sent on

        allow_answer_change: weather or not users are permitted to change their response while the input is running
        """
        #returns 0 for no and 1 for yes to a yes or no question, waits for user to respond
        return await self.basic_multiple_choice(content,["no","yes"],who_chooses,list(utils.emoji_groups.NO_YES_EMOJI),allow_answer_change,response_validator)
    #region text_response overloads
    @overload
    async def basic_text_response(
            self,
            content:str|Address,
            who_chooses:Grouping[Player]|None=...,
            allow_answer_change:bool=...,
            response_validator:ResponseValidator[Send_Text,Player] = ...) -> PlayerDict[str]:
        ...
    @overload
    async def basic_text_response(
            self,
            content:str|Address,
            who_chooses:Player=...,
            allow_answer_change:bool=...,
            response_validator:ResponseValidator[Send_Text,Player] = ...) -> str:
        ...
    #endregion
    async def basic_text_response(
            self,
            content:str|Address,
            who_chooses:Player|Players|None = None,
            allow_answer_change:bool = True,
            response_validator:ResponseValidator[Send_Text,Player] = default_text_validator) -> str|PlayerDict[str]:
        """
        sets up and runs a text input, returning its responses
        
        content: text to send in a message that will be replied to
        
        who_chooses: the list of players whose input matters, if None assumes self.players
        
        channel_id: what channel_id this message should be sent on

        allow_answer_change: weather or not users are permitted to change their response while the input is running
        """
        w = arg_fix_grouping(self.unkicked_players,who_chooses)
        responses:PlayerDictOptional = await self._basic_text_response(
            content=content,
            who_chooses=w,
            allow_answer_change=allow_answer_change,
            response_validator=response_validator

        )
        await self.kick_none_response(responses)
        clean_responses = self.clean_player_dict(responses,w,self.unkicked_players)
        if isinstance(who_chooses,Grouping) or who_chooses is None:
            return clean_responses
        else:
            if who_chooses in clean_responses:
                return clean_responses[who_chooses]
            else:
                return ""#The player did not respond and got kicked, function must still return though
    #endregion
    def allowed_to_speak(self)->bool:
        """
        returns whether the current member function is restricted by being policed
        """
        return self.current_class_execution not in self.classes_banned_from_speaking
    async def basic_send_placement(self,placement:PlayerPlacement):
        """
        takes a placement list and formats it correctly, and sends to the players
        """
        text_list:list[str] = []
        place = 1
        for group in placement:
            if len(group) > 1:
                places = list(ordinate(place+i) for i in range(len(group)))
                text_list.append(f"tied in {wordify_iterable(places)} places we have {mention_participants(group)}")
                place += len(group)
            elif len(group) == 1:
                text_list.append(f"in {ordinate(place)} place we have {mention_participants(group)}")
                place += 1

        return await self.say(f"The placements are: {wordify_iterable(text_list,comma=';')}.")
    async def kick_none_response(self,*args:PlayerMapOptional[Any]|Input[Any,Any,Any],reason:KickReason='timeout'):
        none_responders = set()
        for arg in args:
            responses:PlayerMapOptional[Any]
            if isinstance(arg,Input):
                responses = arg.responses
            else:
                responses = arg
            relevant_players = (player for player in self.unkicked_players if player in responses)
            none_responders.update(set(player for player in relevant_players if responses[player] is None)) 
        await self.kick_players(list(none_responders),reason)
    def max_kick_priority(self) -> int:
        if self.kicked:
            return max(self.kicked[player][0] for player in self.kicked)
        else:
            return 0
    async def kick_players(
            self,
            players:Players,
            reason:KickReason = 'unspecified',
            priority:Optional[int] = None) :
        """
        adds players to the kicked dict with the appropriate priority and reason

        players: a list of players to eliminate
        reason: one of a set list of reasons which might have further implications elsewhere
        priority: where should these players be placed in the order of their elimination, if None, assumes after the last-most eliminated of players so far
        """
        if priority is None:
            priority = self.max_kick_priority() + 1
        for player in players:
            self.kicked[player] = (priority,reason)
        if len(self.unkicked_players) <= 1:
            raise GameEndInsufficientPlayers(f"{mention_participants(players)} being {kick_text[reason]}")
    def clean_player_dict(self,responses:Input[R,Any,Any]|PlayerMapOptional[R],*args:Players) -> PlayerDict[R]:
        clean_responses:PlayerDict = {}
        if isinstance(responses,Input):
            responses = responses.responses
        if args:
            players = list(set.intersection(*list(set(p) for p in args)))
        else:
            players = list(responses)
        for player in players:
            if player in responses:
                if responses[player] is not None:
                    clean_responses[player] = responses[player]
        return clean_responses
    @override
    def __str__(self) -> str:
        return f"{self.__class__.__name__}()"
    
def police_game_callable(func:Callable[P,Awaitable[R]]) -> Callable[P,Awaitable[R]]:
    """
    a wrapper for enabling a function to be policed;
    it modifies the function, so before every execution in registers which class it was most recently defined in as the Game objects self.current_class_execution, and then unregisters it after
    """
    @functools.wraps(func)
    async def wrapped(*args:P.args,**kwargs:P.kwargs) -> R:
        classes:list = list(args[0].__class__.__bases__)
        classes.append(type(args[0].__class__))
        #classes.reverse()
        c = None
        for cls in classes:
            if hasattr(cls,func.__name__):
                c = cls
                break
        assert isinstance(args[0],Game)
        stored = args[0].current_class_execution
        args[0].current_class_execution = c
        to_return = await func(*args,**kwargs)
        args[0].current_class_execution = stored
        return to_return
    return wrapped
