from game.interface_component import Interface_Component

from game import PlayerId, ChannelId, PlayerPlacement, PlayerDict, PlayerDictOptional, KickReason, GameEndException, GameEndInsufficientPlayers, kick_text, score_to_placement
import game.emoji_groups
from game.game_interface import Game_Interface
from game.message import Message
from game.player_input import Player_Input
from game.grammer import ordinate, wordify_iterable
import functools
import sys
import os
import importlib
from inspect import isclass


from typing import Optional, TypeVar, Callable, Awaitable, ParamSpec, overload
from types import ModuleType

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
    @property
    def kicked_players(self) -> list[PlayerId]:
        return list(player for player in self.all_players if player in self.kicked)#maintian order
    @property 
    def unkicked_players(self) -> list[PlayerId]:
        return list(player for player in self.all_players if not player in self.kicked)
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
        await self.game_setup()
        await self.game_intro()
        try:
            await self._run()
        except GameEndException as e:
            self.game_end_exception = e
            await self.basic_send(e.explanation)
        await self.game_unsetup()
        await self.game_outro()
    def generate_placements(self) -> PlayerPlacement:
        return []
    def generate_kicked_placements(self) -> PlayerPlacement:
        return [self.unkicked_players] + score_to_placement({player:self.kicked[player][0] for player in self.kicked},reverse=True)
    @overload
    async def basic_multiple_choice(
            self,content:Optional[str]=...,options:list[str]=...,who_chooses:PlayerId=...,
            emojis:Optional[list[str]]=..., channel_id:Optional[ChannelId]=..., 
            allow_answer_change:bool=...) -> int:
        ...
    @overload
    async def basic_multiple_choice(
            self,content:Optional[str]=...,options:list[str]=...,who_chooses:Optional[list[PlayerId]]=...,
            emojis:Optional[list[str]]=..., channel_id:Optional[ChannelId]=..., 
            allow_answer_change:bool=...) -> PlayerDict[int]:
        ...
    async def basic_multiple_choice(
            self,content:Optional[str] = None,options:list[str] = [],who_chooses:Optional[list[PlayerId]|PlayerId] = None,
            emojis:Optional[list[str]] = None, channel_id:Optional[ChannelId] = None, 
            allow_answer_change:bool = True) -> PlayerDict[int]|int:
        """
        sets up and runs a multiple choice input, returning its responses
        
        content: text to send in a message that will be replied to
        
        options: the list of names of options that the players choose between
        
        who_chooses: the list of players whose input matters, if None assumes self.players
        
        emoji: the list of emoji symbols representing the choices, if None, defaults to colored circles
        
        channel_id: what channel_id this message should be sent on

        allow_answer_change: weather or not users are permitted to change their response while the input is running
        """
        one_response:bool = False
        if not isinstance(who_chooses,list) or who_chooses is None:
            who_chooses = [who_chooses]
            one_response = True
        responses:PlayerDictOptional = await self._basic_multiple_choice(
            content=content,
            options=options,
            who_chooses=who_chooses,
            emojis=emojis,
            channel_id=channel_id,
            allow_answer_change=allow_answer_change

        )
        await self.kick_none_response(responses)
        clean_responses = self.clean_player_dict(responses,who_chooses,self.unkicked_players)
        if not one_response:
            return clean_responses
        else:
            if who_chooses[0] in clean_responses:
                return clean_responses[who_chooses[0]]
            else:
                return -1#The player did not respond and got kicked, function must still return though
    @overload
    async def basic_no_yes(
            self,content:Optional[str]=...,who_chooses:PlayerId=...,
            channel_id:Optional[ChannelId]=..., allow_answer_change:bool=...) -> int:
        ...
    @overload
    async def basic_no_yes(
            self,content:Optional[str]=...,who_chooses:Optional[list[PlayerId]]=...,
            channel_id:Optional[ChannelId]=..., allow_answer_change:bool=...) -> PlayerDict[int]:
        ...
    async def basic_no_yes(
            self,content:Optional[str] = None,who_chooses:Optional[PlayerId|list[PlayerId]] = None,
            channel_id:Optional[ChannelId] = None, allow_answer_change:bool = True) -> int | PlayerDict[int]:
        """
        runs self.basic_multiple_choice with ('no','yes') as the options
        
        content: text to send in a message that will be replied to
        
        who_chooses: the list of players whose input matters, if None assumes self.players
        
        channel_id: what channel_id this message should be sent on

        allow_answer_change: weather or not users are permitted to change their response while the input is running
        """
        #returns 0 for no and 1 for yes to a yes or no question, waits for user to respond
        return await self.basic_multiple_choice(content,["no","yes"],who_chooses,list(game.emoji_groups.NO_YES_EMOJI),channel_id,allow_answer_change)
    @overload
    async def basic_text_response(
            self,content:str,who_chooses:PlayerId=...,
            channel_id:Optional[ChannelId]=..., allow_answer_change:bool=...) -> str:
        ...
    @overload
    async def basic_text_response(
            self,content:str,who_chooses:list[PlayerId]|None=...,
            channel_id:Optional[ChannelId]=..., allow_answer_change:bool=...) -> PlayerDict[str]:
        ...
    async def basic_text_response(
            self,content:str,who_chooses:PlayerId|list[PlayerId]|None = None,
            channel_id:Optional[ChannelId] = None, allow_answer_change:bool = True) -> str|PlayerDict[str]:
        """
        sets up and runs a text input, returning its responses
        
        content: text to send in a message that will be replied to
        
        who_chooses: the list of players whose input matters, if None assumes self.players
        
        channel_id: what channel_id this message should be sent on

        allow_answer_change: weather or not users are permitted to change their response while the input is running
        """
        one_response:bool = False
        if not isinstance(who_chooses,list) or who_chooses is None:
            who_chooses = [who_chooses]
            one_response = True
        responses:PlayerDictOptional = await self._basic_text_response(
            content=content,
            who_chooses=who_chooses,
            channel_id=channel_id,
            allow_answer_change=allow_answer_change

        )
        await self.kick_none_response(responses)
        clean_responses = self.clean_player_dict(responses,who_chooses,self.unkicked_players)
        if not one_response:
            return clean_responses
        else:
            if who_chooses[0] in clean_responses:
                return clean_responses[who_chooses[0]]
            else:
                return ""#The player did not respond and got kicked, function must still return though
    def allowed_to_speak(self)->bool:
        """
        returns whether the current member function is restricted by being policed
        """
        return not self.current_class_execution in self.classes_banned_from_speaking
    async def basic_policed_send(self,content:Optional[str] = None,attatchements_data:list[str] = [],
                   channel_id:Optional[ChannelId] = None):
        """
        self.basic_send if self.allowed_to_speak
        
        content: the text content of the message
        
        attatchements_data: a list of file paths to attatch to the message
        
        channel_id: what channel to send the message on
        """
        if self.allowed_to_speak():
            return await self.basic_send(content,attatchements_data,channel_id)
    async def basic_send_placement(self,placement:PlayerPlacement):
        """
        takes a placement list and formats it correctly, and sends to the players
        """
        text_list:list[str] = []
        place = 1
        for item in placement:
            if isinstance(item,list):
                places = list(ordinate(place+i) for i in range(len(item)))
                text_list.append(f"tied in {wordify_iterable(places)} places we have {self.format_players_md(item)}")
                place += len(item)
            else:
                text_list.append(f"in {ordinate(place)} place we have {self.format_players_md(item)}")
                place += 1

        return await self.basic_send(f"The placements are: {wordify_iterable(text_list,comma=';')}.")
    async def policed_send(self,message:Message):
        """
        a wrapper of self.sender.__call__, for sending Message objects, if not restricted by policing
        """
        if self.allowed_to_speak():
            await self.sender(message)
    async def kick_none_response(self,*args:PlayerDictOptional[R]|Player_Input[R],reason:KickReason='timeout'):
        none_responders = set()
        for arg in args:
            responses:PlayerDictOptional[R]
            if isinstance(arg,Player_Input):
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
            players:list[PlayerId],
            reason:KickReason = 'unspecified',
            priority:Optional[int] = None) :
        """
        adds players to the kicked dict with the approprite priority and reason

        players: a list of players to eliminate
        reason: one of a set list of reasons which might have further implications elsewhere
        priority: where should these players be placed in the order of their elimination, if None, assumes after the lastmost eliminated of players so far
        """
        if priority is None:
            priority = self.max_kick_priority() + 1
        for player in players:
            self.kicked[player] = (priority,reason)
        if len(self.unkicked_players) <= 1:
            raise GameEndInsufficientPlayers(f"{self.sender.format_players_md(players)} being {kick_text[reason]}.")
    def clean_player_dict(self,responses:Player_Input[R]|PlayerDictOptional[R],*args:list[PlayerId]) -> PlayerDict[R]:
        clean_responses:PlayerDict = {}
        if isinstance(responses,Player_Input):
            responses = responses.responses
        if args:
            players = list(set.intersection(*list(set(p) for p in args)))
        else:
            players = list(responses)
        for player in players:
            if player in responses:
                if not responses[player] is None:
                    clean_responses[player] = responses[player]
        return clean_responses
    
    

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
        for clss in classes:
            if hasattr(clss,func.__name__):
                c = clss
                break
        assert isinstance(args[0],Game)
        stored = args[0].current_class_execution
        args[0].current_class_execution = c
        to_return = await func(*args,**kwargs)
        args[0].current_class_execution = stored
        return to_return
    return wrapped
