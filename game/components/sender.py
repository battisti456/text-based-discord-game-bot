from typing import Iterable, override

from game.components.message.message import Message
from utils.grammar import wordify_iterable
from utils.types import PlayerId


class Sender(object):
    """a callable object whose responsibility it is to interpret Messages and display them"""
    def __init__(self):
        pass
    async def __call__(self,message:Message):
        """display Message object for the players according to it's parameters"""
        return await self._send(message)
    async def _send(self,message:Message):
        """lowest level definition of the default Sender's sending capabilities"""
        pass
    def format_players_md(self,players:Iterable[PlayerId]) -> str:
        """format a list of PlayerIds with markdown; --migtht replace with formatter object"""
        return wordify_iterable(players)
    def format_players(self,players:Iterable[PlayerId]) -> str:
        """format a list of PlayerIds without markdown; --migtht replace with formatter object"""
        return wordify_iterable(players)
class Multiple_Sender(Sender):
    def __init__(self,senders:list[Sender]):
        Sender.__init__(self)
        self.senders = senders
    @override
    async def __call__(self, message: Message):
        for sender in self.senders:
            await sender(message)
        return await self._send(message)