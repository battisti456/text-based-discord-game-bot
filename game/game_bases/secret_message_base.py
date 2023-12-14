import game
import game.emoji_groups
import asyncio

from game import userid,channelid,messageid

class Secret_Message_Base(game.Game):
    def __init__(self,gh:game.GH):
        game.Game.__init__(self,gh)
        if not Secret_Message_Base in self.initialized_bases:
            self.initialized_bases.append(Secret_Message_Base)
            self.player_threads:dict[userid,channelid] = {}
    @game.police_messaging
    async def get_secret_thread(self,player:userid,name:str = None) -> channelid:
        if player in self.player_threads:
            thread_id = self.player_threads[player]
        else:
            if self.allowed_to_speak() and name is None:
                name = f"{self.get_user_name(player)}'s secret messages:"
            elif name is None:
                name = ""
            thread_id = await self.create_thread(name)
            await self.invite_to_thread(thread_id,player)
            self.player_threads[player] = thread_id
        return thread_id
    async def secret_send(self,player:userid|list[userid]=None,content:str|dict[userid,str] = None,embed_data:dict|dict[userid,dict] = None,
                          attatchements_data:str|list[str]|dict[userid,str|list[str]] = [],message_id:messageid|dict[userid,messageid] = None) -> messageid|dict[userid,messageid]:
        p:list[userid] = []
        if isinstance(player,int):
            p = [player]
        elif player is None:
            p = list(self.players)
        elif isinstance(player,list):
            p = player
        else:
            p = list(player)
        c:dict[userid,str] = {}
        if isinstance(content,dict):
            c = content
        else:
            c = game.link_to(p,content)
        e:dict[userid,dict] = {}
        if isinstance(embed_data,dict):
            e = embed_data
        else:
            e = game.link_to(p,embed_data)
        a:dict[userid,list[str]|str] = {}
        if attatchements_data is None or isinstance(attatchements_data,list):
            a = game.link_to(p,attatchements_data)
        else:
            a = attatchements_data
        m:dict[userid,message_id] = {}
        if message_id is None or isinstance(message_id,int):
            m = game.link_to(p,message_id)
        else:
            m = message_id

        to_return:dict[userid,messageid] = {}
        for u in p:
            thread_id = await self.get_secret_thread(u)
            m_id = await self.send(content,embed_data,attatchements_data,thread_id,message_id)
            to_return[u] = m_id
        if isinstance(player,int):
            return to_return[player]
        else:
            return to_return
    async def secret_text_response(self,player:userid|list[userid] = None,message:str|dict[userid,str] = None) -> str|dict[userid,str]:
        message = self.make_player_dict(message)
        d_players:list[userid] = self.deduce_players(player,message)
        if not isinstance(player,int):
            return await self.multi_secret_text_response(d_players,message)
        thread_id = await self.get_secret_thread(d_players[0])
        return await self.text_response(message[d_players[0]],d_players[0],thread_id)
    async def secret_multiple_choice(self,player:userid|list[userid] = None,message:str|dict[userid,str] = None,options:list[str]|dict[userid,list[str]] = None,
                                     emojis:list[str]|dict[userid,list[str]] = None) -> int|dict[userid,int]:
        message = self.make_player_dict(message)
        options = self.make_player_dict(options)
        emojis = self.make_player_dict(emojis)
        d_players:list[userid] = self.deduce_players(player,message,options,emojis)
        if not isinstance(player,int):
            return await self.multi_secret_multiple_choice(d_players,message,options,emojis)
        thread_id = await self.get_secret_thread(d_players[0])
        return await self.multiple_choice(message[d_players[0]],options[d_players[0]],d_players[0],emojis[d_players[0]],thread_id)
    async def secret_no_yes(self,player:userid|list[userid] = None,message:str|dict[userid|str] = None) -> int|dict[userid,int]:
        message = self.make_player_dict(message)
        d_players:list[userid] = self.deduce_players(player,message)
        if not isinstance(player,int):
            return await self.multi_secret_no_yes(d_players,message)
        thread_id = await self.get_secret_thread(d_players[0])
        return await self.no_yes(message[d_players[0]],d_players[0],thread_id)
    @game.police_messaging
    async def multi_secret_text_response(self,players:list[userid],messages:dict[userid,str]) -> dict[userid,str]:
        responses:dict[userid,str] = self.make_player_dict(None,players)
        def generate_task(player:userid) -> asyncio.Task:
            async def task():
                responses[player] = await self.text_response(messages[player],player,await self.get_secret_thread(player))
                if self.allowed_to_speak():
                    not_responded = list(p for p in players if responses[player] is None)
                    other_text = ""
                    if not_responded:
                        other_text = f" Still waiting on {self.mention(not_responded)}."
                    await self.send(f"{self.mention(player)} has responded.{other_text}")
            return asyncio.Task(task())
        task_list:list[asyncio.Task] = list(generate_task(player) for player in players)
        await asyncio.wait(task_list)
        return responses
    @game.police_messaging
    async def multi_secret_multiple_choice(self,players:list[userid],messages:dict[userid,str],options:dict[userid,list[str]],
                                           emojis:dict[userid,list[str]]) -> dict[userid,int]:
        responses:dict[userid,str] = self.make_player_dict(None,players)
        def generate_task(player:userid) -> asyncio.Task:
            async def task():
                responses[player] = await self.multiple_choice(messages[player],options[player],player,emojis[player],await self.get_secret_thread(player))
                if self.allowed_to_speak():
                    not_responded = list(p for p in players if responses[players] is None)
                    other_text = ""
                    if not_responded:
                        other_text = f" Still waiting on {self.mention(not_responded)}."
                    await self.send(f"{self.mention(player)} has responded.{other_text}")
            return asyncio.Task(task())
        task_list:list[asyncio.Task] = list(generate_task(player) for player in players)
        await asyncio.wait(task_list)
        return responses
    async def multi_secret_no_yes(self,players:list[userid],messages:dict[userid,str]) -> dict[userid,int]:
        return await self.multi_secret_multiple_choice(players,messages,("no","yes"),game.emoji_groups.NO_YES_EMOJI)    

