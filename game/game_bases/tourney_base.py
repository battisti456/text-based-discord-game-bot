import game
from game import userid




class Tourney_1v1_Base(game.Game):
    def __init__(self,gh:game.GH):
        game.Game.__init__(self,gh)
        
        
    def generate_bracket(self,size:int):
        pass
    async def run(self):
        pass
    async def core_game(self,players:list[int]):
        pass
