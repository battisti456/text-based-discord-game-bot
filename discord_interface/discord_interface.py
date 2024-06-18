from random import shuffle
from typing import Awaitable, Callable, Iterable, Optional, override

import discord
import discord.types
import discord.types.emoji

from discord_interface.discord_sender import Discord_Sender

from game import get_logger
from game.components.game_interface import (
    Game_Interface,
)
from utils.types import ChannelId, MessageId, PlayerId

type AsyncCallback = Callable[[],Awaitable[None]]

logger = get_logger(__name__)

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
            assert isinstance(channel,CompatibleChannels)
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

        
        
