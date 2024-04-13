
from game import PlayerId, ChannelId, PlayerPlacement, PlayerDict, PlayerDictOptional, KickFunc, KickReason
import game.emoji_groups
from game.game_interface import Game_Interface
from game.message import Message, Bullet_Point
from game.sender import Sender
from game.player_input import Player_Single_Selection_Input, Player_Text_Input
from game.grammer import ordinate, wordify_iterable
import functools

from typing import Optional, Iterable, TypeVar, Callable, Awaitable, ParamSpec, overload, Sequence

MULTIPLE_CHOICE_LINE_THRESHOLD = 30
PRIORITY_OF_DEFAULT_KICK = 100#lower happens first

R = TypeVar('R')
P = ParamSpec('P')

class Game(object):
    """
    the base objects all games are built upon
    """
    def __init__(self,gi:Game_Interface):
        if not hasattr(self,'initialized_bases'):#prevents double initialization, although it probably wouldn't hurt anyway
            self.initialized_bases:list[type[Game]] = [Game]
            self.gi = gi
            self.sender:Sender = self.gi.get_sender()
            self.all_players:list[PlayerId] = self.gi.get_players()
            self.current_class_execution:Optional[type[Game]] = None
            self.classes_banned_from_speaking:list[type[Game]] = []

            self.kicked:PlayerDict[tuple[int,KickReason]] = {}
    @property 
    def unkicked_players(self) -> list[PlayerId]:
        return list(player for player in self.all_players if not player in self.kicked)
    async def run(self)->PlayerPlacement:
        """
        runs the currently defined game and returns a list reperesnting a ranking of how the players placed in the game
        """
        return []
    async def run_independant(self):
        """
        executes run and displays the given placement
        """
        placement:PlayerPlacement = await self.run()
        await self.basic_send_placement(placement)
    def format_players_md(self,players:Iterable[PlayerId]) -> str:
        """
        returns the senders fomatting of a list of players with markdown
        """
        return self.sender.format_players_md(players)
    def format_players(self,user_id:list[PlayerId]) -> str:
        """
        returns the senders formatting of a list of players without markdown
        """
        return self.sender.format_players(user_id)
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
        wc:list[PlayerId] = []
        if isinstance(who_chooses,list):
            wc += who_chooses
        elif who_chooses is None:
            wc += self.unkicked_players
        else:
            wc.append(who_chooses)
        emj:list[str] = []
        if emojis is None:
            emj += game.emoji_groups.COLORED_CIRCLE_EMOJI
        else:
            emj += emojis
        bp:list[Bullet_Point] = []
        for i in range(len(options)):
            bp.append(
                Bullet_Point(
                    text = options[i],
                    emoji=emj[i]
                )
            )
        question = Message(
            content = content,
            channel_id=channel_id,
            bullet_points=bp
        )
        await self.sender(question)
        player_input = Player_Single_Selection_Input(
            name = "this multiple choice question",
            gi = self.gi,
            sender = self.sender,
            players=wc,
            message = question,
            allow_edits=allow_answer_change
        )
        await player_input.run()
        if isinstance(who_chooses,list) or who_chooses is None:
            to_return:PlayerDict[int] = {}
            for player in wc:
                value = player_input.responses[player]
                assert not value is None
                to_return[player] = value
            return to_return
        else:
            value = player_input.responses[who_chooses]
            assert not value is None
            return value
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
        wc:list[PlayerId] = []
        if isinstance(who_chooses,list):
            wc += who_chooses
        elif who_chooses is None:
            wc += self.unkicked_players
        else:
            wc.append(who_chooses)
        question = Message(
            content=content,
            channel_id=channel_id
        )
        await self.sender(question)
        player_input = Player_Text_Input(
            name="this text answer question",
            gi = self.gi,
            sender = self.sender,
            players=wc,
            message=question,
            allow_edits=allow_answer_change
        )
        await player_input.run()
        if isinstance(who_chooses,list) or who_chooses is None:
            to_return:PlayerDict[str] = {}
            for player in wc:
                value = player_input.responses[player]
                assert not value is None
                to_return[player] = value
            return to_return
        else:
            value = player_input.responses[who_chooses]
            assert not value is None
            return value

    async def basic_send(self,content:Optional[str] = None,attatchements_data:list[str] = [],
                   channel_id:Optional[ChannelId] = None):
        """
        creates a message with the given parameters and sends it with self.sender
        
        content: the text content of the message
        
        attatchements_data: a list of file paths to attatch to the message
        
        channel_id: what channel to send the message on
        """
        message = Message(
            content = content,
            attach_paths=attatchements_data,
            channel_id=channel_id
        )
        await self.sender(message)
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
    async def send(self,message:Message):
        """
        a wrapper of self.sender.__call__, for sending Message objects
        """
        await self.sender(message)
    async def policed_send(self,message:Message):
        """
        a wrapper of self.sender.__call__, for sending Message objects, if not restricted by policing
        """
        if self.allowed_to_speak():
            await self.sender(message)
    async def kick_none_response(self,responses:PlayerDictOptional):
        relevant_players = (player for player in self.unkicked_players if player in responses)
        none_responders = (player for player in relevant_players if responses[player] is None)
        await self.kick_players(list(none_responders))
    def max_kick_priority(self) -> int:
        if self.kicked:
            return max(self.kicked[player][0] for player in self.kicked)
        else:
            return 0
    async def kick_players(
            self,
            players:list[PlayerId],
            reason:KickReason = 'unspecified',
            priority:Optional[int] = None) -> bool:
        """
        adds players to the kicked dict with the approprite priority and reason
        returns false if this leaves 1 or 0 unkicked players
        true if there are 2 or more remaining players

        players: a list of players to eliminate
        reason: one of a set list of reasons which might have further implications elsewhere
        priority: where should these players be placed in the order of their elimination, if None, assumes after the lastmost eliminated of players so far
        """
        if priority is None:
            priority = self.max_kick_priority() + 1
        for player in players:
            self.kicked[player] = (priority,reason)
        return len(self.unkicked_players) > 1

    
    

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