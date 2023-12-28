from game import PlayerId
from game.message import Message
from game.grammer import wordify_iterable

from typing import Iterable

class Sender(object):
    #A callable object used to display a Message to player
    def __init__(self):
        pass
    async def __call__(self,message:Message):
        return await self._send(message)
    async def _send(self,message:Message):
        pass
    def format_players(self,players:Iterable[PlayerId]) -> str:
        return wordify_iterable(players)
class Multiple_Sender(Sender):
    def __init__(self,senders:list[Sender]):
        Sender.__init__(self)
        self.senders = senders
    async def __call__(self, message: Message):
        for sender in self.senders:
            await sender(message)
        return await self._send(message)
