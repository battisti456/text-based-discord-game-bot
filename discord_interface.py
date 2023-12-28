from typing import Optional
from game.game_interface import Channel_Limited_Game_Interface, Channel_Limited_Interface_Sender
from game.message import Message, Add_Bullet_Points_To_Content_Alias_Message
from game.interaction import Interaction

import discord
from math import ceil
from random import shuffle

from game import PlayerId, MessageId, ChannelId

MESSAGE_MAX_LENGTH = 1800#actually 2000, but I leave extra for split indicators

def discord_message_populate_interaction(
        payload:discord.Message, interaction:Interaction):
    interaction.player_id = payload.author.id
    interaction.channel_id = payload.channel.id
    interaction.content = payload.content
    interaction.interaction_id = payload.id
    if (not (payload.reference is None) and 
            not (payload.reference.cached_message is None)):
            interaction.reply_to_message_id = payload.reference.cached_message.id
    return interaction

class Discord_Sender(Channel_Limited_Interface_Sender):
    def __init__(self,gi:'Discord_Game_Interface'):
        Channel_Limited_Interface_Sender.__init__(self,gi)
        self.client = gi.client
        self.default_channel = gi.channel_id
    async def _send(self, message: Message):
        if not message.content is None:
            if len(message.content) > MESSAGE_MAX_LENGTH:
                sub_messages = message.split(
                    length=MESSAGE_MAX_LENGTH,
                    add_start="--MESSAGE TOO LONG. WAS SPLIT--\n",
                    add_end="\n--END MESSAGE--",
                    add_join_end="\n--SPLIT END--",
                    add_join_start="\n--SPLIT START--")
                for sub_message in sub_messages:
                    await self._send(sub_message)
        else:
            if message.bullet_points:
                message = Add_Bullet_Points_To_Content_Alias_Message(message)
            if message.channel_id is None:
                assert isinstance(self.default_channel,int)
                channel = self.client.get_channel(self.default_channel)
            else:
                assert isinstance(message.channel_id,int)
                channel = self.client.get_channel(message.channel_id)
            assert isinstance(channel,discord.TextChannel)
            attachments= []
            for path in message.attach_paths:
                attachments.append(discord.File(path))
            if message.message_id is None:#new message
                await self.client.wait_until_ready()
                discord_message = await channel.send(content=message.content,files = attachments)
                message.message_id = discord_message.id
            else:#edit old message
                assert isinstance(message.message_id,int)
                await self.client.wait_until_ready()
                discord_message:discord.Message = await channel.fetch_message(message.message_id)
                await discord_message.edit(content=message.content,attachments=attachments)
                message.message_id = discord_message.id
            if message.bullet_points:
                for bp in message.bullet_points:
                    if not bp.emoji is None:
                        emoji = discord.PartialEmoji(name = bp.emoji)
                        await self.client.wait_until_ready()
                        await discord_message.add_reaction(emoji)

class Discord_Game_Interface(Channel_Limited_Game_Interface):
    def __init__(self,channel_id:ChannelId,players:list[PlayerId]):
        Channel_Limited_Game_Interface.__init__(self)
        self.channel_id = channel_id
        self.players = players
        
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents = intents)
        self.default_sender = Discord_Sender(self)

        @self.client.event
        async def on_ready():#triggers when client is logged into discord
            pass
        @self.client.event
        async def on_message(payload:discord.Message):#triggers when client
            if (self.client.user is None or 
                payload.author.id != self.client.user.id):
                interaction = Interaction('send_message')
                discord_message_populate_interaction(payload,interaction)
                await self._trigger_action(interaction)
        @self.client.event
        async def on_raw_message_edit(payload:discord.RawMessageUpdateEvent):
            if (not payload.cached_message is None and
                (self.client.user is None or 
                 payload.cached_message.author.id != self.client.user.id)):
                interaction = Interaction('edit_message')
                discord_message_populate_interaction(
                    payload.cached_message,interaction)
                interaction.content = payload.data['content']
                interaction.interaction_id = payload.message_id
                await self._trigger_action(interaction)
        @self.client.event
        async def on_raw_message_delete(payload:discord.RawMessageDeleteEvent):
            if (not payload.cached_message is None and
                (self.client.user is None or 
                 payload.cached_message.author.id != self.client.user.id)):
                interaction = Interaction('delete_message')
                discord_message_populate_interaction(
                    payload.cached_message,interaction)
                interaction.interaction_id = payload.message_id
                await self._trigger_action(interaction)
        @self.client.event
        async def on_raw_reaction_add(payload:discord.RawReactionActionEvent):
            pass
        @self.client.event
        async def on_raw_reaction_remove(payload:discord.RawReactionActionEvent):
            pass
    async def run(self):
        pass
    async def new_channel(self, name: Optional[str] = None, who_can_see: Optional[list[PlayerId]] = None) -> ChannelId | None:
        assert isinstance(self.channel_id,int)
        main_channel = self.client.get_channel(self.channel_id)
        assert isinstance(main_channel,discord.TextChannel)
        thread = None
        while thread is None:
            if name is None:
                name = ""
            await self.client.wait_until_ready()
            thread = await main_channel.create_thread(name = name)
        if not who_can_see is None:
            for player in who_can_see:
                assert isinstance(player,int)
                user = self.client.get_user(player)
                assert not user is None
                await self.client.wait_until_ready()
                await thread.add_user(user)
        return thread.id
    def get_players(self) -> list[PlayerId]:
        players = self.players.copy()
        shuffle(players)
        return players

        
        
