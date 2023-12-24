from game.game_interface import Game_Interface, Interface_Sender
from game.message import Message
from game.interaction import Interaction

import discord
from math import ceil

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

class Discord_Sender(Interface_Sender):
    def __init__(self,gi:'Discord_Game_Interface'):
        Interface_Sender.__init__(self,gi)
        self.client = gi.client
        self.default_channel = gi.channel_id
    async def _send(self, message: Message):
        if not message.content is None:
            if len(message.content) > MESSAGE_MAX_LENGTH:
                sub_messages = message.split(length=MESSAGE_MAX_LENGTH,add_join="\n--SPLIT--")
                sub_messages[-1].message_id = message.message_id
                for sub_message in sub_messages:
                    await self._send(sub_message)
                message.message_id = sub_messages[-1].message_id
        else:
            await self.client.wait_until_ready()
            if message.channel_id is None:
                channel = self.client.get_channel(self.default_channel)
            else:
                channel = self.client.get_channel(message.channel_id)
            assert isinstance(channel,discord.TextChannel)
            attachments= []
            for path in message.attach_paths:
                attachments.append(discord.File(path))

            if message.message_id is None:#new message
                discord_message = await channel.send(content=message.content,files = attachments)
                message.message_id = discord_message.id
            else:#edit old message
                discord_message:discord.Message = await channel.fetch_message(message.message_id)
                await discord_message.edit(content=message.content,attachments=attachments)
                message.message_id = discord_message.id

class Discord_Game_Interface(Game_Interface):
    def __init__(self,channel_id:ChannelId,players:list[PlayerId]):
        Game_Interface.__init__(self)
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
        
