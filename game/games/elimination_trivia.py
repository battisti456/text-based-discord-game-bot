from game import PlayerId
from game.game_bases import Elimination_Base, Trivia_Base
from game.game_interface import Game_Interface

class Elimination_Trivia(Elimination_Base,Trivia_Base):
    def __init__(self,gi:Game_Interface):
        Elimination_Base.__init__(self,gi)
        Trivia_Base.__init__(self,gi)
    async def game_intro(self):
        await self.basic_send(
            "# This is a game of elimination trivia.\n" +
            "I will ask you a trivia question, and you will react with the appropriate option.\n" +
            "Once everyone not yet eliminated has answered, I will reveal the correct answer and eliminate those who got it wrong.\n" +
            "Feel free to respond even once you are eliminated, but I will not be counting those.\n" +
            "Let's begin!"
        )
    async def core_game(self,remaining_players:list[PlayerId]) -> list[PlayerId]:
        player_correct:dict[PlayerId,bool] = await self.ask_trivia(remaining_players)
        return list(player for player in remaining_players if not player_correct[player])