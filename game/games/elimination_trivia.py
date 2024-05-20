from typing import override

from game.components.game_interface import Game_Interface
from game.game_bases import Elimination_Base, Trivia_Base
from utils.types import PlayerDict


class Elimination_Trivia(Elimination_Base,Trivia_Base):
    def __init__(self,gi:Game_Interface):
        Elimination_Base.__init__(self,gi)
        Trivia_Base.__init__(self,gi)
    @override
    async def game_intro(self):
        await self.basic_send(
            "# This is a game of elimination trivia.\n" +
            "I will ask you a trivia question, and you will react with the appropriate option.\n" +
            "Once everyone not yet eliminated has answered, I will reveal the correct answer and eliminate those who got it wrong.\n" +
            "Feel free to respond even once you are eliminated, but I will not be counting those.\n" +
            "Let's begin!"
        )
    @override
    async def core_game(self):
        player_correct:PlayerDict[bool] = await self.basic_ask_trivia(self.unkicked_players)
        await self.eliminate(tuple(player for player in self.unkicked_players if not player_correct[player]))