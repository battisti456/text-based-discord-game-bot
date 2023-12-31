import game
import game.emoji_groups
import asyncio

from game import PlayerId,ChannelId,MessageId
from typing import Callable, Awaitable

class Secret_Message_Base(game.Game):
    def __init__(self,gh:game.GH):
        game.Game.__init__(self,gh)
        if not Secret_Message_Base in self.initialized_bases:
            self.initialized_bases.append(Secret_Message_Base)
            self.player_threads:dict[PlayerId,ChannelId] = {}
    @game.police_game_callable
    async def get_secret_thread(self,player:PlayerId,name:str = None) -> ChannelId:
        if player in self.player_threads:
            thread_id = self.player_threads[player]
        else:
            if self.allowed_to_speak() and name is None:
                name = f"{self.format_players(player)}'s secret messages:"
            elif name is None:
                name = ""
            thread_id = await self.create_thread(name)
            await self.invite_to_thread(thread_id,player)
            self.player_threads[player] = thread_id
        return thread_id
    async def secret_send(self,player:PlayerId|list[PlayerId]=None,content:str|dict[PlayerId,str] = None,embed_data:dict|dict[PlayerId,dict] = None,
                          attatchements_data:str|list[str]|dict[PlayerId,str|list[str]] = [],message_id:MessageId|dict[PlayerId,MessageId] = None) -> MessageId|dict[PlayerId,MessageId]:
        p:list[PlayerId] = []
        if isinstance(player,int):
            p = [player]
        elif player is None:
            p = list(self.players)
        elif isinstance(player,list):
            p = player
        else:
            p = list(player)
        c:dict[PlayerId,str] = {}
        if isinstance(content,dict):
            c = content
        else:
            c = game.link_to(p,content)
        e:dict[PlayerId,dict] = {}
        if isinstance(embed_data,dict):
            e = embed_data
        else:
            e = game.link_to(p,embed_data)
        a:dict[PlayerId,list[str]|str] = {}
        if attatchements_data is None or isinstance(attatchements_data,list):
            a = game.link_to(p,attatchements_data)
        else:
            a = attatchements_data
        m:dict[PlayerId,message_id] = {}
        if message_id is None or isinstance(message_id,int):
            m = game.link_to(p,message_id)
        else:
            m = message_id

        to_return:dict[PlayerId,MessageId] = {}
        for u in p:
            thread_id = await self.get_secret_thread(u)
            m_id = await self.basic_send(content,embed_data,attatchements_data,thread_id,message_id)
            to_return[u] = m_id
        if isinstance(player,int):
            return to_return[player]
        else:
            return to_return
    async def secret_text_response(self,player:PlayerId|list[PlayerId] = None,message:str|dict[PlayerId,str] = None, allow_answer_change:bool = True,
                                   sync_lock:Callable[[bool],Awaitable[bool]] = None,store_in:dict[PlayerId,str] = None) -> str|dict[PlayerId,str]:
        message = self.make_player_dict(message)
        d_players:list[PlayerId] = self.deduce_players(player,message)
        if not isinstance(player,int):
            return await self.multi_secret_text_response(d_players,message,allow_answer_change,sync_lock,store_in)
        thread_id = await self.get_secret_thread(d_players[0])
        return await self.basic_text_response(message[d_players[0]],d_players[0],thread_id,allow_answer_change,sync_lock,store_in)
    async def secret_multiple_choice(self,player:PlayerId|list[PlayerId] = None,message:str|dict[PlayerId,str] = None,options:list[str]|dict[PlayerId,list[str]] = None,
                                     emojis:list[str]|dict[PlayerId,list[str]] = None,allow_answer_change:bool=True,
                                     sync_lock:Callable[[bool],Awaitable[bool]] = None, store_in:dict[PlayerId,int] = None) -> int|dict[PlayerId,int]:
        message = self.make_player_dict(message)
        options = self.make_player_dict(options)
        emojis = self.make_player_dict(emojis)
        d_players:list[PlayerId] = self.deduce_players(player,message,options,emojis)
        if not isinstance(player,int):
            return await self.multi_secret_multiple_choice(d_players,message,options,emojis,allow_answer_change,sync_lock,store_in)
        thread_id = await self.get_secret_thread(d_players[0])
        return await self.basic_multiple_choice(message[d_players[0]],options[d_players[0]],d_players[0],emojis[d_players[0]],thread_id,allow_answer_change,sync_lock,store_in)
    async def secret_no_yes(self,player:PlayerId|list[PlayerId] = None,message:str|dict[PlayerId|str] = None,allow_answer_change:bool = True,
                            sync_lock:Callable[[bool],Awaitable[bool]] = None, store_in:dict[PlayerId,int] = None) -> int|dict[PlayerId,int]:
        message = self.make_player_dict(message)
        d_players:list[PlayerId] = self.deduce_players(player,message)
        if not isinstance(player,int):
            return await self.multi_secret_no_yes(d_players,message,allow_answer_change,sync_lock,store_in)
        thread_id = await self.get_secret_thread(d_players[0])
        return await self.basic_no_yes(message[d_players[0]],d_players[0],thread_id,allow_answer_change,sync_lock,store_in)
    async def multi_secret_text_response(
        self,players:list[PlayerId],messages:dict[PlayerId,str],allow_answer_change:bool,
        sync_lock:Callable[[bool],Awaitable[bool]],store_in:dict[PlayerId,int]) -> dict[PlayerId,str]:
        responses:dict[PlayerId,str] = {}
        if store_in is None:
            responses:dict[PlayerId,str] = self.make_player_dict(None,players)
        else:
            responses = store_in
            for user in players:
                if not user in responses:
                    responses[user] = None
        all_done:game.IsDone = game.IsDone(False)
        sub_sync_lock:Callable[[bool],Awaitable[bool]] = game.sub_sync_lock_maker(sync_lock,all_done,responses,players)
        def generate_task(player:PlayerId) -> asyncio.Task:
            async def task():
                await self.basic_text_response(messages[player],player,await self.get_secret_thread(player),
                                         allow_answer_change,sub_sync_lock,responses)
            return asyncio.Task(task())
        task_list:list[asyncio.Task] = list(generate_task(player) for player in players)

        task_list.append(asyncio.Task((await self.wait_message(responses,players,sub_sync_lock))()))
            
        await asyncio.wait(task_list)
        return responses
    async def multi_secret_multiple_choice(
        self,players:list[PlayerId],messages:dict[PlayerId,str],options:dict[PlayerId,list[str]],
        emojis:dict[PlayerId,list[str]],allow_answer_change:bool,sync_lock:Callable[[bool],Awaitable[bool]],
        store_in:dict[PlayerId,int]) -> dict[PlayerId,int]:

        responses:dict[PlayerId,str] = {}
        if store_in is None:
            responses = self.make_player_dict(None,players)
        else:
            responses = store_in
            for player in players:
                if not player in responses:
                    responses[player] = None
        
        all_done:game.IsDone = game.IsDone(False)
        sub_sync_lock:Callable[[bool],Awaitable[bool]] = game.sub_sync_lock_maker(sync_lock,all_done,responses,players)
        
        def generate_task(player:PlayerId) -> asyncio.Task:
            async def task():
                await self.basic_multiple_choice(
                    messages[player],options[player],player,emojis[player],
                    await self.get_secret_thread(player),allow_answer_change,sub_sync_lock,responses)
            return asyncio.Task(task())
        task_list:list[asyncio.Task] = list(generate_task(player) for player in players)

        task_list.append(asyncio.Task((await self.wait_message(responses,players,sub_sync_lock))()))

        await asyncio.wait(task_list)
        return responses
    async def multi_secret_no_yes(self,players:list[PlayerId],messages:dict[PlayerId,str],allow_answer_change:bool,
                                  sync_lock:Callable[[bool],Awaitable[bool]],store_in:dict[PlayerId,int]) -> dict[PlayerId,int]:
        return await self.multi_secret_multiple_choice(
            players,messages,("no","yes"),game.emoji_groups.NO_YES_EMOJI,
            allow_answer_change,sync_lock,store_in)    

