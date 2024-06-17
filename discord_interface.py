from dataclasses import dataclass
from random import shuffle
from time import sleep
from typing import Awaitable, Callable, Iterable, Optional, override

import discord

from game import get_logger
from game.components.game_interface import (
    Game_Interface,
)
from game.components.interaction import Interaction
from game.components.message import Add_Bullet_Points_To_Content_Alias_Message
from game.components.send import Send_Address, Sendable, Sender
from game.components.send.old_message import _Old_Message
from game.components.send.sendable.prototype_sendables import (
    Attach_Files,
    Text,
    With_Options,
)
from game.components.send.sendable.sendables import (

)
from utils.grammar import wordify_iterable
from utils.types import ChannelId, MessageId, PlayerId

type AsyncCallback = Callable[[],Awaitable[None]]
DiscordChannel = discord.TextChannel|discord.Thread

logger = get_logger(__name__)

MESSAGE_MAX_LENGTH = 1800#actually 2000, but I leave extra for split indicators
SLEEP429 = 10
BLANK_TEXT = " "

def discord_message_populate_interaction(
        payload:discord.Message, interaction:Interaction):
    interaction.player_id = payload.author.id#type: ignore
    interaction.channel_id = payload.channel.id#type: ignore
    interaction.content = payload.content
    interaction.interaction_id = payload.id#type: ignore
    if (
        payload.reference is not None
        ):
        reply_id:MessageId|None = payload.reference.message_id#type:ignore
        if reply_id is None:
            logger.warning("received a message with a reference but no reference.message_id")
        else:
            interaction.reply_to_message_id = reply_id
    return interaction
async def discord_message_emoji_order(
        payload:discord.Message, user_id:int) -> list[str]:
    emoji:list[str] = []
    for reaction in payload.reactions:
        async for user in reaction.users():
            if user.id == user_id:
                emoji.append(str(reaction.emoji))
                break
    return emoji
@dataclass(frozen=True)
class Discord_Message():
    message_id:int
    channel_id:int

@dataclass(frozen=True)
class Discord_Address(Send_Address):
    messages:tuple[Discord_Message,...]

class Discord_Sender(Sender[Discord_Address]):
    def __init__(self,gi:'Discord_Game_Interface'):
        Sender.__init__(self)
        self.gi = gi
        self.client = gi.client
        self.default_channel = gi.channel_id
    @override
    async def generate_address(self, channel: ChannelId | None = None, length:int = 1) -> Discord_Address:
        if channel is None:
            channel = self.default_channel
        
    @override
    async def _send(self, sendable: Sendable, address: Discord_Address|None = None) -> Discord_Address:
        if isinstance(sendable,_Old_Message):
            ...
        else:#unknown type, just go by subtypes
            if isinstance(sendable,Text):
                ...
            if isinstance(sendable,With_Options):
                ...
            if isinstance(sendable,Attach_Files):
                ...
        if address is None:
            ...
        else:
            return address
    async def _old_send(self, sendable: _Old_Message, address:Discord_Address):
        channel = self.client.get_channel(address.messages[0].channel_id)
        assert isinstance(channel,DiscordChannel)
        attachments:list[discord.File] = []
        if isinstance(sendable,Attach_Files):
            for path in sendable.attach_files:
                attachments.append(discord.File(path))
        await self.client.wait_until_ready()
        discord_message:discord.Message = await channel.fetch_message(address.messages[0].message_id)
        await discord_message.edit(
            content=str(BLANK_TEXT if not isinstance(sendable,Text) else sendable.text),
            attachments=attachments
            )
        if isinstance(sendable,With_Options):
            for bp in sendable.with_options:
                if bp.emoji is not None:
                    emoji = discord.PartialEmoji(name = bp.emoji)
                    success = False
                    while not success:
                        try:
                            await self.client.wait_until_ready()
                            await discord_message.add_reaction(emoji)
                            success = True
                        except Exception as e:#not sure what the actual exceptions are
                            logger.error(f"failed to add bullet points due to:\n{type(e)}: {e}")
                            sleep(SLEEP429)
    @override
    def format_players_md(self, players: Iterable[PlayerId]) -> str:
        return wordify_iterable(f"<@{player}>" for player in players)
    @override
    def format_players(self,players:Iterable[PlayerId]) -> str:
        player_names:list[str] = []
        for player in players:
            assert isinstance(player,int)
            user = self.client.get_user(player)
            if user is not None:
                player_names.append(user.display_name)
            else:
                player_names.append(str(player))
        return wordify_iterable(player_names)


class Discord_Game_Interface(Game_Interface):
    def __init__(self,channel_id:ChannelId,players:list[PlayerId]):
        Game_Interface.__init__(self)
        self.channel_id = channel_id
        self.players = players
        
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        self.client = discord.Client(intents = intents)
        self.default_sender = Discord_Sender(self)

        self.first_initialization = True
        self.on_start_callbacks:list[AsyncCallback] = []
        #region 
        @self.client.event
        async def on_ready():#triggers when client is logged into discord
            if self.first_initialization:
                for callback in self.on_start_callbacks:
                    await callback()
                self.first_initialization = False
            else:
                await self.reconnect()
        @self.client.event
        async def on_message(payload:discord.Message):#triggers when client
            if (self.client.user is None or 
                payload.author.id != self.client.user.id):
                interaction = Interaction('send_message')
                discord_message_populate_interaction(payload,interaction)
                await self._trigger_action(interaction)
        @self.client.event
        async def on_raw_message_edit(payload:discord.RawMessageUpdateEvent):
            if (
                payload.cached_message is not None and
                (self.client.user is None or 
                payload.cached_message.author.id != self.client.user.id)):
                interaction = Interaction('delete_message')
                discord_message_populate_interaction(
                    payload.cached_message,interaction)
                await self._trigger_action(interaction)
                interaction.interaction_type = 'send_message'
                if 'content' in payload.data: #sometimes it isn't aparently?
                    interaction.content = payload.data['content']
                interaction.interaction_id = payload.message_id#type:ignore
                await self._trigger_action(interaction)
        @self.client.event
        async def on_raw_message_delete(payload:discord.RawMessageDeleteEvent):
            if (
                payload.cached_message is not None and
                (self.client.user is None or 
                payload.cached_message.author.id != self.client.user.id)):
                interaction = Interaction('delete_message')
                discord_message_populate_interaction(
                    payload.cached_message,interaction)
                interaction.interaction_id = payload.message_id#type:ignore
                await self._trigger_action(interaction)
        @self.client.event
        async def on_raw_reaction_add(payload:discord.RawReactionActionEvent):
            if (self.client.user is None or payload.user_id != self.client.user.id):
                emoji:str = str(payload.emoji)
                interaction = Interaction('select_option')
                interaction.content = emoji
                interaction.player_id = payload.user_id#type:ignore
                interaction.reply_to_message_id = payload.message_id#type:ignore
                interaction.interaction_id = payload.emoji.id#type:ignore
                
                message = self.find_tracked_message(payload.message_id)#type:ignore
                if message is not None:
                    if message.with_options is not None:
                        for i in range(len(message.with_options)):
                            if message.with_options[i].emoji == emoji:
                                interaction.choice_index = i
                                break
                        if interaction.choice_index is not None:
                            await self._trigger_action(interaction)
        @self.client.event
        async def on_raw_reaction_remove(payload:discord.RawReactionActionEvent):
            if (self.client.user is None or payload.user_id != self.client.user.id):
                emoji:str = str(payload.emoji)
                interaction = Interaction('deselect_option')
                interaction.content = emoji
                interaction.player_id = payload.user_id#type:ignore
                interaction.reply_to_message_id = payload.message_id#type:ignore
                interaction.interaction_id = payload.emoji.id#type:ignore
                
                message = self.find_tracked_message(payload.message_id)#type:ignore
                if message is not None:
                    if message.with_options is not None:
                        for i in range(len(message.with_options)):
                            if message.with_options[i].emoji == emoji:
                                interaction.choice_index = i
                                break
                        if interaction.choice_index is not None:
                            await self._trigger_action(interaction)
        #endregion
    @override
    async def reset(self):
        await super().reset()
        await self.client.wait_until_ready()
        assert isinstance(self.channel_id,int)
        channel = self.client.get_channel(self.channel_id)
        assert isinstance(channel,discord.TextChannel)
        for thread in channel.threads:
            await thread.delete()
    async def reconnect(self):
        """this method is called by discord.py when we have gotten on_ready more than once to hopefully ensure the game remains functional"""
        #ISSUE1: after reconnect message.reference seems to sometimes be None when it shouldn't be
        #POSSIBLE SOLUTION: fetch all currently tracked messages to hopefully pu them in the discord catch or some-such
        return
        logger.warning("reconnecting after discord service reconnect")
        logger.warning("attempting to fetch tracked messages")
        channels:set[ChannelId|None] = set(message.channel_id for message in self.tracked_messages)
        for channel in channels:
            channel_id:ChannelId = channel if channel is not None else self.channel_id
            assert channel_id is int
            channel = self.client.get_channel(channel_id)
            assert isinstance(channel,DiscordChannel)
            for message_id,message in ((message.message_id,message) for message in self.tracked_messages if message.channel_id == channel):
                if message_id is not None:
                    assert message_id is int
                    partial = channel.get_partial_message(message_id)
                    try:
                        await partial.fetch()
                    except discord.NotFound:
                        logger.error(f"failed to find message {message}")
                    except discord.HTTPException:
                        logger.error(f"failed to fetch message {message}")

    async def _infer_option_order(self,channel_id:ChannelId,message_id:MessageId) -> list[str]:#very very slow
        assert isinstance(channel_id,int)
        await self.client.wait_until_ready()
        channel = await self.client.fetch_channel(channel_id)
        assert isinstance(message_id,int)
        assert isinstance(channel,(discord.TextChannel,discord.Thread))
        await self.client.wait_until_ready()
        message = await channel.fetch_message(message_id)

        assert self.client.user is not None
        emoji:list[str] = []
        for reaction in message.reactions:
            async for user in reaction.users():
                if user.id == self.client.user.id:
                    emoji.append(str(reaction.emoji))
                    break
        return emoji
    @override
    async def _new_channel(self, name: Optional[str], who_can_see: Optional[Iterable[PlayerId]]) -> ChannelId:
        assert isinstance(self.channel_id,int)
        main_channel = self.client.get_channel(self.channel_id)
        assert isinstance(main_channel,discord.TextChannel)
        thread = None
        while thread is None:
            if name is None:
                name = ""
            await self.client.wait_until_ready()
            thread = await main_channel.create_thread(
                name = name,
                auto_archive_duration=10080#waits 7 days until it hides the thread
                )
        if who_can_see is not None:
            for player in who_can_see:
                assert isinstance(player,int)
                user = self.client.get_user(player)
                assert user is not None#user not found
                await self.client.wait_until_ready()
                await thread.add_user(user)
        return thread.id#type:ignore
    @override
    def get_players(self) -> frozenset[PlayerId]:
        players = self.players.copy()
        shuffle(players)
        return frozenset(players)
    def on_start(self,callback:AsyncCallback) -> AsyncCallback:
        self.on_start_callbacks.append(callback)
        return callback

        
        
