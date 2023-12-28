from typing import Any,Callable,Awaitable, Optional
from game import PlayerId, MessageId, ChannelId
from game.sender import Sender
from game.message import Message
from game.interaction import Interaction, InteractionType, INTERACTION_TYPES
from game.grammer import wordify_iterable

Action = Callable[[Interaction],Awaitable]


class Interface_Sender(Sender):
    def __init__(self,gi:'Game_Interface'):
        Sender.__init__(self)
        self.gi = gi
    async def __call__(self,message:Message) -> Any:
        return await self._send(message)

class Game_Interface(object):
    def __init__(self):
        self.actions:dict[InteractionType,list[Action]] = {}
        self.clear_actions()
        self.default_sender = Interface_Sender(self)
    def clear_actions(self):
        for action in INTERACTION_TYPES:
            self.actions[action] = []
    async def run(self):
        pass
    def get_sender(self) -> Interface_Sender:
        return self.default_sender
    async def _trigger_action(
            self,interaction:Interaction):
        for action in self.actions[interaction.interaction_type]:
            await action(interaction)
    def on_action(self,action_type:InteractionType) -> Callable[[Action],Action]:
        def wrapper(func:Action) -> Action:
            self.actions[action_type].append(func)
            return func
        return wrapper
    def player_id_to_str(self,player:PlayerId) -> str:
        return str(player)
    def get_players(self) -> list[PlayerId]:
        return []
    async def new_channel(self,name:Optional[str] = None, who_can_see:Optional[list[PlayerId]] = None) -> ChannelId|None:
        pass

class Channel_Limited_Interface_Sender(Interface_Sender): 
    def __init__(self,gi:'Channel_Limited_Game_Interface'):
        Interface_Sender.__init__(self,gi)
    async def __call__(self,message:Message):
        if not message.players_who_can_see is None and message.channel_id is None:
            assert isinstance(self.gi,Channel_Limited_Game_Interface)
            message.channel_id = await self.gi.who_can_see_channel(message.players_who_can_see)
        return await self._send(message)

class Channel_Limited_Game_Interface(Game_Interface):
    #a special kind of game interface which uses channels to limit who_can_see on Message
    def __init__(self):
        Game_Interface.__init__(self)
        self.who_can_see_dict:dict[frozenset[PlayerId],ChannelId] = {}
        self.default_sender = Channel_Limited_Interface_Sender(self)
    async def who_can_see_channel(self,players:list[PlayerId]) -> ChannelId:
        fr_players = frozenset(players)
        if fr_players in self.who_can_see_dict:
            return self.who_can_see_dict[fr_players]
        else:
            channel = await self.new_channel(
                f"{wordify_iterable(self.player_id_to_str(player) for player in players)}'s Private Channel",
                players
            )
            assert not channel is None
            self.who_can_see_dict[fr_players] = channel
            return channel


