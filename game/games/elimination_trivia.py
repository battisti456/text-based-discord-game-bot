import game
from game import userid
from game.game_bases import Elimination_Base
from game.game_bases import Trivia_Base

from typing import Iterable

class Elimination_Trivia(Elimination_Base,Trivia_Base):
    def __init__(self,gh:game.GH):
        Elimination_Base.__init__(self,gh)
        Trivia_Base.__init__(self,gh)
    async def game_intro(self):
        await self.send(
            """# This is a game of elimination trivia.
            I will ask you a trivia question, and you will react with the appropriate option.
            Once everyone not yet eliminated has answered, I will reveal the correct answer and eliminate those who got it wrong.
            Feel free to respond even once you are eliminated, but I will not be counting those.
            Let's begin!"""
        )
    async def core_game(self,remaining_players:list[userid]) -> list[userid]:
        player_correct:dict[userid,bool] = await self.ask_trivia(remaining_players)
        return list(player for player in remaining_players if not player_correct[player])