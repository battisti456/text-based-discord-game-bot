from game import *
import game.emoji_groups

import asyncio
import uuid

from typing import Sequence

MULTIPLE_CHOICE_LINE_THRESHOLD = 30

class Game(object):
    def __init__(self,gh:game_handler.Game_Handler):
        if not hasattr(self,'initialized_bases'):#prevents double initialization, although it probably wouldn't hurt anyway
            self.initialized_bases:list[type[Game]] = [Game]
            self.gh = gh
            self.logger = self.gh.logger
            self.message_actions:dict[messageid,Callable[[str,userid,messageid],None]] = {}#message id replying to, function
            self.reaction_actions:dict[messageid,Callable[[str,userid],None]] = {}#message reacting to, function
            self.unreaction_actions:dict[messageid,Callable[[str,userid],None]] = {}#message remove reaction from, function
            self.edit_actions:dict[messageid,Callable[[str,userid,messageid],None]] = {}
            self.delete_actions:dict[messageid,Callable[[str,userid,messageid],None]] = {}
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
    async def on_message(self,message:str,reply_id:messageid,user_id:userid,message_id:messageid):
        #on_message action, should be called by gh
        self.logger.debug(f"on_message called in reply to {reply_id} from {user_id} with '{message}' via {message_id}")
        if reply_id in self.message_actions:
            self.logger.debug(f"Calling message action {reply_id} from {user_id} with '{message}'")
            await self.message_actions[reply_id](message,user_id,message_id)
    async def on_unreaction(self,emoji:str,message_id:messageid,user_id:userid):
        self.logger.debug(f"on_unreaction called for {message_id} from {user_id} with '{emoji}'")
        if message_id in self.unreaction_actions:
            self.logger.debug(f"Calling unreaction action for {message_id} from {user_id} with '{emoji}'")
            await self.unreaction_actions[message_id](emoji,user_id)
    async def on_edit(self,message:str,reply_id:messageid,user_id:userid,message_id:messageid):
        self.logger.debug(f"on_edit called in reply to {reply_id} from {user_id} with '{message}' via {message_id}")
        if reply_id in self.edit_actions:
            self.logger.debug(f"Calling edit action in reply to {reply_id} from {user_id} with '{message}' via {message_id}")
            await self.edit_actions[reply_id](message,user_id,message_id)
    async def on_delete(self,message:str,reply_id:messageid,user_id:userid,message_id:messageid):
        self.logger.debug(f"on_delete called in reply to {reply_id} from {user_id} with '{message}' via {message_id}")
        if reply_id in self.edit_actions:
            self.logger.debug(f"Calling delete action in reply to {reply_id} from {user_id} with '{message}' via {message_id}")
            await self.delete_actions[reply_id](message,user_id,message_id)
    def mention(self,user_id:userid|Iterable[userid]) -> str:
        #returns a string with properly formatted text for a discord mention
        if isinstance(user_id,int):
            return f"<@{user_id}>"
        else:#it is an iterable
            return wordify_iterable(self.mention(uid) for uid in user_id)
    async def multiple_choice(self,message:str = None,options:list[str] = [],who_chooses:userid|list[userid] = None,
                              emojis:str|list[str] = None, channel_id:channelid = None, allow_answer_change:bool = True,
                              sync_lock:Callable[[str,dict[userid,int],bool],bool] = None) -> int | dict[userid,int]:
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
        if sync_lock is None and len(wc) == 1:#no reason to allow answer change
            allow_answer_change = False
        emj = emj[0:len(options)]
        self.logger.info(f"Beggining multiple choice monitoring for answers {options} via emojis {emj} from users {wc}.")
        choice_response:dict[userid,int] = {}
        for user_id in wc:
            choice_response[user_id] = None
        
        if any(len(option) > MULTIPLE_CHOICE_LINE_THRESHOLD for option in options):
            option_text = (
                "**The options are:**\n" +
                '\n'.join(f"{emj[i]} (*{options[i]}*)" for i in range(len(options)))
            )
        else:
            option_text = (
                f"**The options are:**\n"+ 
                wordify_iterable((f"{emj[i]} (*{options[i]}*)" for i in range(len(options))),"or"))
        allow_answer_change_text = ""
        if allow_answer_change:
            allow_answer_change_text = "You may change your answers."
        def question_text() -> str:
            players_not_answered:list = list(player for player in choice_response if choice_response[player] is None)
            waiting_on_text = "All players have reacted."
            if players_not_answered:
                waiting_on_text = f"Awaiting reaction from {self.mention(players_not_answered)}. {allow_answer_change_text}"
            return f"{message}\n{waiting_on_text}\n{option_text}"
        message_id = await self.send(question_text(),channel_id = channel_id)
        async def reaction_action(emoji:str,user_id:int):
            self.logger.debug(f"Reaction action called by {user_id} with {emoji}.")
            if user_id in choice_response and emoji in emj:
                if allow_answer_change or choice_response[user_id] is None:
                    choice_response[user_id] = emj.index(emoji)
                    await self.send(question_text(),message_id=message_id)
                    if not choice_response[user_id] is None:
                        self.logger.info(
                            f"User {user_id} added reaction {emoji} to multiple choice response, selecting '{options[choice_response[user_id]]}'")
        async def unreaction_action(emoji:str,user_id:userid):
            if user_id in choice_response:
                if emoji == emj[choice_response[user_id]] and allow_answer_change:
                    choice_response[user_id] = None
                    await self.send(question_text(),message_id=message_id)
                    self.logger.info(f"User {user_id} removed reaction {emoji} from multiple choice response, selecting nothing.")
        self.add_reaction_action(message_id,reaction_action)
        self.add_unreaction_action(message_id,unreaction_action)
        await self.gh.add_reaction(emj,message_id)
        keep_going = True
        while keep_going:
            #await self.wait(CHECK_TIME)
            await self.do_nothing()
            is_done = not any(choice_response[user_id] is None for user_id in wc)
            if sync_lock is None:
                keep_going = not is_done
            else:
                keep_going = not await sync_lock(message,choice_response,is_done)
            #self.logger.debug(f"Waiting for emoji responses on {message_id} from {wc}. Currently {choice_response}.")
        self.remove_reaction_action(message_id)
        self.remove_unreaction_action(message_id)
        if isinstance(who_chooses,int):
            return choice_response[who_chooses]
        else:
            return choice_response
    async def no_yes(self,message:str = None,who_chooses:userid|list[userid] = None,channel_id:channelid = None,
                     allow_answer_change:bool = True, sync_lock:Callable[[str,dict[userid,int]],bool] = None) -> int | dict[userid,int]:
        #returns 0 for no and 1 for yes to a yes or no question, waits for user to respond
        return await self.multiple_choice(message,("no","yes"),who_chooses,game.emoji_groups.NO_YES_EMOJI,channel_id,allow_answer_change,sync_lock)
    async def text_response(
            self,message:str,who_responds:userid|list[userid]|None = None,
            channel_id:channelid = None, allow_answer_change:bool = True, 
            sync_lock:Callable[[str,dict[userid,str],bool],bool] = None) -> str | dict[userid,str]:
        users = self.deduce_players(who_responds)
        responses:dict[userid,str] = self.make_player_dict(None,users)
        if sync_lock is None and len(users) == 1:#no reason to allow answer change
            allow_answer_change = False
        allow_answer_change_text = ""
        if allow_answer_change:
            allow_answer_change_text = "You may change your answer."
        def question_text() -> str:
            players_not_answered:list = list(player for player in responses if responses[player] is None)
            waiting_on_text = "All players have responded."
            if players_not_answered:
                waiting_on_text = f"Awaiting reply from {self.mention(players_not_answered)}. {allow_answer_change_text}"
            return f"{message}\n{waiting_on_text}"
        message_id = await self.send(question_text(),channel_id = channel_id)
        async def message_action(message:str,user_id:userid,author_message_id:messageid):
            if user_id in users:
                if allow_answer_change or responses[user_id] == None:
                    responses[user_id] = message
                    self.logger.info(f"{user_id} set their response to '{message}' via {author_message_id}.")
                    await self.send(question_text(),channel_id = channel_id,message_id=message_id)
        async def edit_action(message:str,user_id:userid,author_message_id:messageid):
            if user_id in users and allow_answer_change:
                responses[user_id] = message
                self.logger.info(f"{user_id} changed their response to '{message}' via {author_message_id}.")
                await self.send(question_text(),channel_id = channel_id,message_id=message_id)
        async def delete_action(message:str,user_id:userid,author_message_id:messageid):
            if user_id in users and allow_answer_change:
                responses[user_id] = None
                self.logger.info(f"{user_id} deleted their response  {author_message_id}.")
                await self.send(question_text(),channel_id = channel_id,message_id=message_id)
        self.add_message_action(message_id,message_action)
        self.add_edit_action(message_id,edit_action)
        self.add_delete_action(message_id,delete_action)
        keep_going = True
        while keep_going:
            #await self.wait(CHECK_TIME)
            await self.do_nothing()
            is_done = not any(responses[user] is None for user in users)
            if sync_lock is None:
                keep_going = not is_done
            else:
                keep_going = not await sync_lock(message,responses,is_done)
            #self.logger.debug(f"Waiting for text responses on {message_id} from {users}. Currently {responses}.")
        self.remove_message_action(message_id)
        self.remove_edit_action(message_id)
        self.remove_delete_action(message_id)
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
    async def do_nothing(self):
        async def do_nothing():
            pass
        await asyncio.wait([asyncio.Task(do_nothing())])
    def add_reaction_action(self,message_id:messageid,reaction_action:Callable[[str,userid],None]):
        #adds a function from the dict of responses to reactions
        self.reaction_actions[message_id] = reaction_action
    def remove_reaction_action(self,message_id:messageid):
        #removes a function from the dict of responses to reactions
        del self.reaction_actions[message_id]
    def add_message_action(self,message_id:messageid,message_action:Callable[[str,userid,messageid],None]):
        #adds a function from the dict of responses to messages
        self.message_actions[message_id] = message_action
    def remove_message_action(self,message_id:messageid):
        #removes a function from the dict of responses to messages
        del self.message_actions[message_id]
    def add_edit_action(self,message_id:messageid,message_action:Callable[[str,userid,messageid],None]):
        #adds a function from the dict of responses to message edits
        self.edit_actions[message_id] = message_action
    def remove_edit_action(self,message_id:messageid):
        #removes a function from the dict of responses to message edits
        del self.edit_actions[message_id]
    def add_delete_action(self,message_id:messageid,message_action:Callable[[str,userid,messageid],None]):
        #adds a function from the dict of responses to message deletions
        self.delete_actions[message_id] = message_action
    def remove_delete_action(self,message_id:messageid):
        #removes a function from the dict of responses to message deletions
        del self.delete_actions[message_id]
    def add_unreaction_action(self,message_id:messageid,unreaction_action:Callable[[str,userid],None]):
        self.unreaction_actions[message_id] = unreaction_action
    def remove_unreaction_action(self,message_id:messageid):
        del self.unreaction_actions[message_id]
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