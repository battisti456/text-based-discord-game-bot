import discord

import logging

import random

from typing import Sequence

#import game


class Game_Handler(object):
    def __init__(self,config:dict):
        self.config = config
        self.current_game = None
        self.next_game = None
        
        self.logger = logging.getLogger('gamebot_logger')
        logger_file_handler = logging.FileHandler(self.config["log_file"], mode='w',encoding='utf-8')
        logging_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        logger_file_handler.setFormatter(logging_formatter)
        self.logger.addHandler(logger_file_handler)
        self.logger.setLevel(self.config["log_level"])

        intents = discord.Intents.all()
        self.client = discord.Client(intents = intents)#https://discordpy.readthedocs.io/en/stable/api.html#audiosource

        self.current_threads = set()

        async def main_loop():
            self.logger.info("Main loop has started.")
            await self.client.wait_until_ready()
            while not self.client.is_closed():
                await self.clean_up()
                self.logger.info(f"Now running {self.current_game.__class__.__name__}.")
                if not self.current_game is None:
                    rank = await self.current_game.run()
                    await self.current_game.send_rank(rank)
                if self.next_game is not None:
                    self.current_game = self.next_game
                    self.next_game = None
                else:
                    self.logger.warning(f"No next game was set!.")
                    return
        @self.client.event
        async def on_ready():#triggers when client is logged into discord
            self.logger.info(f"Now ready as {self.client.user}.")
            await self.client.wait_until_ready()
            self.client.loop.create_task(main_loop())#needs to be in async func
        @self.client.event
        async def on_message(payload:discord.Message):#triggers when client detects a message being sent
            self.logger.debug(f"Received message '{payload.content}' from {payload.author}.")
            if(payload.author.id != self.client.user.id) and not self.current_game is None:
                reply_id = None
                if payload.reference is not None:
                    if not payload.reference.cached_message is None:
                        reply_id = payload.reference.cached_message.id
                await self.current_game.on_message(payload.content,reply_id,payload.author.id)
        @self.client.event
        async def on_raw_reaction_add(payload:discord.RawReactionActionEvent):#trigger when client detects a reaction being added
            self.logger.debug(f"Registered reaction {payload.emoji} on message {payload.message_id} from user {payload.user_id} in channel {payload.channel_id}")
            if(payload.user_id != self.client.user.id) and not self.current_game is None:
                await self.current_game.on_reaction(payload.emoji.__str__(),payload.message_id,payload.user_id)
    def run(self):
        self.client.run(self.config["token"])
    async def clean_up(self):
        await self.client.wait_until_ready()
        channel = self.client.get_channel(self.config["channel_id"])
        for thread in channel.threads:
            await thread.delete()
    def set_next_game(self,next_game):
        self.next_game = next_game
    async def add_reaction(self,emoji:str|tuple|list,message_id:int):#tested
        #adds all the emojis in emoji in order as reactions to the given message
        await self.client.wait_until_ready()
        self.logger.debug(f"Adding reactions to message {message_id}: {emoji}.")
        reactions_to_add = []
        if isinstance(emoji,str):
            reactions_to_add = emoji.split()
        else:
            reactions_to_add = emoji
        await self.client.wait_until_ready()
        channel = self.client.get_channel(self.config["channel_id"])
        message = channel.get_partial_message(message_id)
        await message.fetch()
        for reaction in reactions_to_add:
            self.logger.debug(f"Adding \"{reaction}\" to message {message.id} on channel {channel.id}.")
            await message.add_reaction(reaction)
    async def create_thread(self,name:str) -> int:
        #creates a private thread on the default channel and return its id
        self.logger.debug(f"Creating a thread called {name}.")
        await self.client.wait_until_ready()
        channel = self.client.get_channel(self.config["channel_id"])
        thread = await channel.create_thread(name = name)
        while thread is None:
            thread = await channel.create_thread(name = name)
        self.logger.debug(f"Created thread {thread.id} on channel {channel.id}.")
        self.current_threads.add(thread.id)
        return thread.id
    async def invite_to_thread(self,thread_id:int,user_ids:int|tuple):
        #invites user or users to a thread by mentioning them
        self.logger.debug(f"Inviting users {user_ids} to thread {thread_id}.")
        await self.client.wait_until_ready()
        if type(user_ids) is int:
            user_ids = (user_ids,)
        channel = self.client.get_channel(self.config["channel_id"])
        thread = channel.get_thread(thread_id)
        for user_id in user_ids:
            user = self.client.get_user(user_id)
            await thread.add_user(user)
            user = await thread.fetch_member(user_id)
            self.logger.debug(f"User '{user.id}' has been added to thread {thread.id}.")
    async def delete_thread(self,thread_id:int):
        #deletes the thread given
        await self.client.wait_until_ready()
        channel = self.client.get_channel(self.config["channel_id"])
        thread = channel.get_thread(thread_id)
        self.logger.debug(f"Deleting thread {thread_id} with last message \"{thread.last_message.content}.\"")
        thread.delete()
        if thread_id in self.current_threads:
            self.current_threads.remove(thread_id)
    async def delete_message(self,message_id:int, channel_id:int = None):
        await self.client.wait_until_ready()
        if channel_id is None:
            channel_id = self.config["channel_id"]
        channel = self.client.get_channel(channel_id)
        message:discord.Message = channel.fetch_message(message_id)
        await message.delete()
    def get_players(self)->tuple[int]:
        player_list = list(self.config["players"][player] for player in self.config["players"])
        random.shuffle(player_list)
        return tuple(player_list)
    async def send(self,content:str|None = None,embed_data:None|dict = None,attatchements_data:Sequence[str]|str = [],channel_id:int|None = None,message_id:int|None = None) -> int:
        await self.client.wait_until_ready()
        if channel_id is None:
            channel = self.client.get_channel(self.config["channel_id"])
        else:
            channel = self.client.get_channel(channel_id)
        if not embed_data is None:
            embed = discord.Embed()
            embed.from_dict(embed_data)
        else:
            embed = None
        if isinstance(attatchements_data,str):
            attatchments = [discord.File(attatchements_data)]
        else:
            attatchments= []
            for attatchment_data in attatchements_data:
                attatchments.append(discord.File(attatchment_data))

        if message_id is None:
            message = await channel.send(content=content,embed=embed,files = attatchments)
            return message.id
        else:
            message:discord.Message = channel.fetch_message(message_id)
            await message.edit(content=content,embed=embed,attatchments=attatchments)
            #await message.send()
            return message.id
    def get_user_name(self,user_id:int) -> str:
        user:discord.User = self.client.get_user(user_id)
        return user.name
