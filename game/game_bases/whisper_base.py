from typing import Unpack

from game.components.game_interface import Game_Interface
from game.game import Game
from utils.types import PlayerId
from smart_text import TextLike
from game.components.send import MakeSendableArgs


class Whisper_Base(Game):
    def __init__(self,gi:Game_Interface):
        Game.__init__(self,gi)
        if Whisper_Base not in self.initialized_bases:
            self.initialized_bases.append(Whisper_Base)
    async def w_say(self,text:TextLike,player:PlayerId):
        address = await self.sender.generate_address(for_players=frozenset((player,)))
        await self.say(text,address)
    async def w_send(self,player:PlayerId,**kwargs:Unpack[MakeSendableArgs]):
        address = await self.sender.generate_address(for_players=frozenset((player,)))
        await self.send(address=address,**kwargs)