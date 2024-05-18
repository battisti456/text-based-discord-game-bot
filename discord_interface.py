from typing import Optional, Iterable, override
from game.components.game_interface import Channel_Limited_Game_Interface, Channel_Limited_Interface_Sender
from game.components.message import Message, Add_Bullet_Points_To_Content_Alias_Message
from game.components.interaction import Interaction
from game.utils.grammer import wordify_iterable

import discord
from random import shuffle

from game.utils.types import PlayerId, MessageId, ChannelId
from game import get_logger

logger = get_logger(__name__)

MESSAGE_MAX_LENGTH = 1800#actually 2000, but I leave extra for split indicators

def discord_message_populate_interaction(
        payload:discord.Message, interaction:Interaction):
    interaction.player_id = payload.author.id#type: ignore
    interaction.channel_id = payload.channel.id#type: ignore
    interaction.content = payload.content
    interaction.interaction_id = payload.id#type: ignore
    if (
        not (payload.reference is None)
        ):
        reply_id:MessageId|None = payload.reference.message_id#type:ignore
        if reply_id is None:
            logger.warning(f"received a message with a reference but no reference.message_id")
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


class Discord_Sender(Channel_Limited_Interface_Sender):
    def __init__(self,gi:'Discord_Game_Interface'):
        Channel_Limited_Interface_Sender.__init__(self,gi)
        self.client = gi.client
        self.default_channel = gi.channel_id
    @override
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
                return
        if message.bullet_points:
            message = Add_Bullet_Points_To_Content_Alias_Message(message)
        if message.channel_id is None:
            assert isinstance(self.default_channel,int)
            channel = self.client.get_channel(self.default_channel)
        else:
            assert isinstance(message.channel_id,int)
            channel = self.client.get_channel(message.channel_id)
        assert isinstance(channel,(discord.TextChannel,discord.Thread))
        attachments:list[discord.File] = []
        if not message.attach_paths is None:
            for path in message.attach_paths:
                attachments.append(discord.File(path))
        if message.message_id is None and not message.reply_to_id is None:
            await self.client.wait_until_ready()
            assert isinstance(message.reply_to_id,int)
            to_reply = await channel.fetch_message(message.reply_to_id)
            discord_message = await to_reply.reply(
                content=message.content,
                files=attachments
            )
            message.message_id = discord_message.id#type: ignore
        elif message.message_id is None:#new message
            await self.client.wait_until_ready()
            discord_message = await channel.send(
                content=message.content 
                if not message.content in (None,'') else "--empty--",
                files = attachments)
            message.message_id = discord_message.id#type:ignore
        else:#edit old message
            assert isinstance(message.message_id,int)
            await self.client.wait_until_ready()
            discord_message:discord.Message = await channel.fetch_message(message.message_id)
            await discord_message.edit(content=message.content,attachments=attachments)
            message.message_id = discord_message.id#type:ignore
        if message.bullet_points:
            for bp in message.bullet_points:
                if not bp.emoji is None:
                    emoji = discord.PartialEmoji(name = bp.emoji)
                    await self.client.wait_until_ready()
                    await discord_message.add_reaction(emoji)
    @override
    def format_players_md(self, players: Iterable[PlayerId]) -> str:
        return wordify_iterable(f"<@{player}>" for player in players)
    @override
    def format_players(self,players:Iterable[PlayerId]) -> str:
        player_names:list[str] = []
        for player in players:
            assert isinstance(player,int)
            user = self.client.get_user(player)
            if not user is None:
                player_names.append(user.display_name)
            else:
                player_names.append(str(player))
        return wordify_iterable(player_names)


class Discord_Game_Interface(Channel_Limited_Game_Interface):
    def __init__(self,channel_id:ChannelId,players:list[PlayerId]):
        Channel_Limited_Game_Interface.__init__(self)
        self.channel_id = channel_id
        self.players = players
        
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

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
                interaction = Interaction('send_message')
                discord_message_populate_interaction(
                    payload.cached_message,interaction)
                if 'content' in payload.data: #sometimes it isn't aparently?
                    interaction.content = payload.data['content']
                interaction.interaction_id = payload.message_id#type:ignore
                await self._trigger_action(interaction)
        @self.client.event
        async def on_raw_message_delete(payload:discord.RawMessageDeleteEvent):
            if (not payload.cached_message is None and
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
                if not message is None:
                    if not message.bullet_points is None:
                        for i in range(len(message.bullet_points)):
                            if message.bullet_points[i].emoji == emoji:
                                interaction.choice_index = i
                                break
                        if not interaction.choice_index is None:
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
                if not message is None:
                    if not message.bullet_points is None:
                        for i in range(len(message.bullet_points)):
                            if message.bullet_points[i].emoji == emoji:
                                interaction.choice_index = i
                                break
                        if not interaction.choice_index is None:
                            await self._trigger_action(interaction)
    @override
    async def reset(self):
        await super().reset()
        await self.client.wait_until_ready()
        assert isinstance(self.channel_id,int)
        channel = self.client.get_channel(self.channel_id)
        assert isinstance(channel,discord.TextChannel)
        for thread in channel.threads:
            await thread.delete()
    async def _infer_option_order(self,channel_id:ChannelId,message_id:MessageId) -> list[str]:#very very slow
        assert isinstance(channel_id,int)
        await self.client.wait_until_ready()
        channel = await self.client.fetch_channel(channel_id)
        assert isinstance(message_id,int)
        assert isinstance(channel,(discord.TextChannel,discord.Thread))
        await self.client.wait_until_ready()
        message = await channel.fetch_message(message_id)

        assert not self.client.user is None
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
            thread = await main_channel.create_thread(name = name)
        if not who_can_see is None:
            for player in who_can_see:
                assert isinstance(player,int)
                user = self.client.get_user(player)
                assert not user is None#user not found
                await self.client.wait_until_ready()
                await thread.add_user(user)
        return thread.id#type:ignore
    @override
    def get_players(self) -> frozenset[PlayerId]:
        players = self.players.copy()
        shuffle(players)
        return frozenset(players)

        
        
