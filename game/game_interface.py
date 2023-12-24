from typing import Any,Callable,Awaitable,Literal, NewType
from game import PlayerId, MessageId
from game.sender import Sender
from game.message import Message
from game.interaction import Interaction, InteractionType, INTERACTION_TYPES

Action = Callable[[Interaction],Awaitable]


class Interface_Sender(Sender):
    def __init__(self,gi:'Game_Interface'):
        Sender.__init__(self)
        self.gi = gi
    async def __call__(self,message:Message) -> Any:
        self.gi.track_message(message)
        return await self._send(message)

class Game_Interface(object):
    def __init__(self):
        self.tracked_messages:list[Message] = []
        self.actions:dict[InteractionType,list[Action]] = {}
        self.clear_actions()
        self.default_sender = Interface_Sender(self)
    def track_message(self,message:Message):
        self.tracked_messages.append(message)
    def untrack_message(self,message:Message):
        self.tracked_messages.remove(message)
    def clear_tracked_messages(self):
        self.tracked_messages = []
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
    def find_message_by_id(self,message_id:MessageId) -> Message|None:
        for message in self.tracked_messages:
            if message.message_id == message_id:
                return message
        return None

