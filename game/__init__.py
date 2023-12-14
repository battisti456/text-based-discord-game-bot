from collections.abc import Iterator
import game_handler
import asyncio
from time import sleep
from typing import Callable, Iterable, Sequence, TypeVar, ParamSpec, NewType, Any
import functools

import game.emoji_groups


import uuid


userid = NewType("userid",int)
messageid = NewType("messageid",int)
channelid = NewType("channelid",int)

P = ParamSpec('P')
R = TypeVar('R')


GH = game_handler.Game_Handler
CHECK_TIME = 0.5

class Game(object):
    def __init__(self,gh:game_handler.Game_Handler):
        if not hasattr(self,'gh'):#prevents double initialization, although it probably wouldn't hurt anyway
            self.gh = gh
            self.logger = self.gh.logger
            self.message_actions:dict[messageid,Callable[[str,userid],None]] = {}#message id replying to, function
            self.reaction_actions:dict[messageid,Callable[[str,userid],None]] = {}#message reacting to, function
            self.players:tuple[userid] = self.gh.get_players()
            self.current_class_execution:type[Game] = None
            self.classes_banned_from_speaking:list[type[Game]] = []
            self.config:dict[str,Any] = self.gh.config
    async def run(self)->Iterable[int]:
        pass
    async def on_reaction(self,emoji:str,message_id:messageid,user_id:userid):
        #on reaction, should be called by gh
        self.logger.debug(f"on_message called for {message_id} from {user_id} with '{emoji}'")
        if message_id in self.reaction_actions:
            await self.reaction_actions[message_id](emoji,user_id)
    async def on_message(self,message:str,reply_id:messageid,user_id:userid):
        #on_message action, should be called by gh
        self.logger.debug(f"on_message called for {reply_id} from {user_id} with '{message}'")
        if reply_id in self.message_actions:
            self.logger.debug(f"Calling message action {reply_id} from {user_id} with '{message}'")
            await self.message_actions[reply_id](message,user_id)
    def mention(self,user_id:userid|Iterable[userid]) -> str:
        #returns a string with properly formatted text for a discord mention
        if isinstance(user_id,int):
            return f"<@{user_id}>"
        else:#it is an iterable
            return wordify_iterable(self.mention(uid) for uid in user_id)

    async def multiple_choice(self,message:str = None,options:list[str] = [],who_chooses:userid|list[userid] = None,
                              emojis:str|list[str] = None, channel_id:channelid = None) -> int | dict[userid,int]:
        #returns the indexof the choice a user would like from choices, waits for user to respond
        if isinstance(who_chooses,list):
            wc = who_chooses
        elif isinstance(who_chooses,int):
            wc = [who_chooses]
        elif who_chooses is None:
            wc = self.players
        else:
            wc = list(who_chooses)
        if isinstance(emojis,str):
            emj = emojis.split()
        elif emojis is None:
            emj = list(game.emoji_groups.COLORED_CIRCLE_EMOJI)
        else:
            emj = list(emojis)
        emj = emj[0:len(options)]
        choice_response:dict[userid,int] = {}
        for user_id in wc:
            choice_response[user_id] = None
        async def reaction_action(emoji:str,user_id:int):
            self.logger.debug(f"Reaction action called by {user_id} with {emoji}.")
            if user_id in choice_response and emoji in emj:
                choice_response[user_id] = emj.index(emoji)
        to_say = (message+ 
                  f"\n**I would like {self.mention(wc)} to please react to this message with their answer(s)! The options are:**\n"+ 
                  wordify_iterable((f"{emj[i]} (*{options[i]}*)" for i in range(len(options))),"or"))
        message_id = await self.send(to_say,channel_id = channel_id)
        await self.gh.add_reaction(emj,message_id)
        self.add_reaction_action(message_id,reaction_action)
        while any(choice_response[user_id] == None for user_id in choice_response):
            await self.wait(CHECK_TIME)
            self.logger.debug(f"Waiting for emoji responses on {message_id} from {wc}. Currently {choice_response}.")
        self.remove_reaction_action(message_id)
        if isinstance(who_chooses,int):
            return choice_response[who_chooses]
        else:
            return choice_response
    async def no_yes(self,message:str = None,who_chooses:userid|list[userid] = None,channel_id:channelid = None) -> int | dict[userid,int]:
        #returns 0 for no and 1 for yes to a yes or no question, waits for user to respond
        return await self.multiple_choice(message,("no","yes"),who_chooses,game.emoji_groups.NO_YES_EMOJI,channel_id)
    async def text_response(self,message:str,who_responds:userid|list[userid]|None = None,channel_id:channelid = None) -> str | dict[userid,str]:
        users = self.deduce_players(who_responds)
        responses:dict[userid,str] = self.make_player_dict(None,users)
        async def message_action(message:str,user_id:userid):
            self.logger.debug(f"Message action called by {user_id} with '{message}'.")
            if user_id in users:
                responses[user_id] = message
        message_id = await self.send(message+
                                     f"""
**I would like {self.mention(who_responds)} to please reply to this message with their answer(s)**.""",channel_id = channel_id)
        self.add_message_action(message_id,message_action)
        while any(responses[user] is None for user in users):
            await self.wait(CHECK_TIME)
            self.logger.debug(f"Waiting for text responses on {message_id} from {users}. Currently {responses}.")
        self.remove_message_action(message_id)
        if isinstance(who_responds,int):
            return responses[who_responds]
        else:
            return responses
    async def wait(self,seconds:int):
        #async safe wait function (wrapper of asyncio.wait)
        async def wait():
            sleep(seconds)
        task = asyncio.create_task(wait())
        await asyncio.wait([task],timeout=seconds)
    def add_reaction_action(self,message_id:messageid,reaction_action:Callable[[str,userid],None]):
        #adds a function from the dict of responses to reactions
        self.reaction_actions[message_id] = reaction_action
    def remove_reaction_action(self,message_id:messageid):
        #removes a function from the dict of responses to reactions
        del self.reaction_actions[message_id]
    def add_message_action(self,message_id:messageid,message_action:Callable[[str,userid],None]):
        #adds a function from the dict of responses to messages
        self.message_actions[message_id] = message_action
    def remove_message_action(self,message_id:messageid):
        #removes a function from the dict of responses to messages
        del self.message_actions[message_id]
    async def create_thread(self,name:str = None) -> channelid:
        #creates a private thread
        return await self.gh.create_thread(name)
    async def invite_to_thread(self,thread_id:channelid,user_id:userid|Iterable[userid]):
        #invites a user (or users) to a private thread
        await self.gh.invite_to_thread(thread_id,user_id)
    def temp_file_path(self,type:str) -> str:
        #returns a (probably) unique file name in the temp folder
        return f"{self.config['temp_path']}//{uuid.uuid4()}{type}"
    async def send(self,content:str = None,embed_data:dict = None,attatchements_data:Sequence[str]|str = [],
                   channel_id:channelid = None,message_id:messageid = None) -> messageid:
        #a wrapper of Game.gh.send
        return await self.gh.send(content,embed_data,attatchements_data,channel_id,message_id)
    def allowed_to_speak(self)->bool:
        #checks if current_class execution tag set from police_messaging is one of the classes banned from speaking
        return not self.current_class_execution in self.classes_banned_from_speaking
    async def policed_send(self,content:str = None,embed_data:dict = None,attatchements_data:Sequence[str]|str = [],
                           channel_id:channelid = None,message_id:messageid = None) -> messageid:
        #only sends if allowed_to_speak
        if self.allowed_to_speak():
            return await self.send(content,embed_data,attatchements_data,channel_id,message_id)
    def get_user_name(self,user_id:userid) -> str:
        return self.gh.get_user_name(user_id)
    def deduce_players(self,*args:list[list[userid]|userid|dict[userid,Any]]) -> list[userid]:
        #chooses the subset of players that appear in every item
        players:list[userid] = None
        for item in args:
            if item is None or isinstance(item,str):
                continue
            try:
                list_format_item = list(item)
            except TypeError:
                list_format_item = [item]
            if players is None:
                players = list_format_item
            else:
                for player in self.players:
                    if player in players and not player in list_format_item:
                        players.remove(player)
        if players is None:
            players = list(self.players)
        return players
    def is_player_dict(self,item) -> bool:
        #returns whether an item is a dictionary containing only keys of players
        item_is_player_dict = False
        if isinstance(item,dict):
            item_is_player_dict = True
            for i in item:
                if not i in self.players:
                    item_is_player_dict = False
                    break
        return item_is_player_dict
    def make_player_dict(self,item:dict[userid,R]|R,players:list[userid] = None) -> dict[userid,R]:
        #returns an item as player dict of all players or given players, using None for the value where the value is undefined
        if players is None:
            players = list(self.players)
        
        to_return:dict[userid,R] = {}
        item_is_player_dict = self.is_player_dict(item)
        for player in players:
            if item_is_player_dict:
                if player in item:
                    to_return[player] = item[player]
            else:
                to_return[player] = item
        return to_return
    async def send_rank(self,rank:list[userid,list[userid]],channel_id:channelid = None,message_id:messageid = None) -> messageid:
        text_list:list[str] = []
        place = 1
        for item in rank:
            if isinstance(item,list):
                places = list(ordinate(place+i) for i in range(len(item)))
                text_list.append(f"tied in {wordify_iterable(places)} places we have {self.mention(item)}")
                place += len(item)
            else:
                text_list.append(f"in {ordinate(place)} place we have {self.mention(item)}")
                place += 1
        return await self.send(f"The placements are: {wordify_iterable(text_list,comma=';')}.")
    async def delete_message(self,message_id:messageid,channel_id:channelid = None):
        await self.gh.delete_message(message_id,channel_id)
                    
def police_messaging(func:Callable[P,R]) -> Callable[P,R]:
    #Adds the class the function was fist defined in to current_class_execution, only to be used on asynchronous Game methods
    @functools.wraps(func)
    async def wrapped(*args:P.args,**kwargs:P.kwargs) -> R:
        classes:list = list(args[0].__class__.__bases__)
        classes.append(type(args[0].__class__))
        #classes.reverse()
        for clss in classes:
            if hasattr(clss,func.__name__):
                c = clss
                break
        args[0].current_class_execution = c
        to_return = await func(*args,**kwargs)
        args[0].current_class_execution = None
        return to_return
    return wrapped

def wordify_iterable(values:Iterable[str],operator:str = 'and',comma:str = ",") -> str:
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
    for value in values:
        d[value] = link_to
    return d

def one_depth_len(lst:list[R|list[R]]) -> int:
    to_return = 0
    for item in lst:
        try:
            to_return += len(item)
        except TypeError:
            to_return += 1
    return to_return
def one_depth_flat(lst:list[R|list[R]]) -> list[R]:
    to_return:list[R] = []
    for item in lst:
        try:
            to_return += item
        except TypeError:
            to_return.append(item)
    return to_return
def ordinate(num:int|str) -> str:
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
    return num + ordinal
    


import game.game_bases
import game.games