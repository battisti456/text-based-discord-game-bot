from typing import Optional, override

from game.game import Game, Game_Interface


class Rounds_Base(Game):
    def __init__(self,gi:Game_Interface):
        Game.__init__(self,gi)
        if Rounds_Base not in self.initialized_bases:
            self.initialized_bases.append(Rounds_Base)
            self.num_rounds:Optional[int] = None
            """num_rounds to run for, if None run forever, if 1 it won't announce round number"""
            self.round_word:str = 'round'
    def string_round(self,round:int) -> str:
        return f"{self.round_word} {round}"
    async def core_game(self):
        ...
    async def start_round(self):
        ...
    async def end_round(self):
        ...
    @override
    async def _run(self):
        round:int = 0
        of_str:str = ""
        if isinstance(self.num_rounds,int):
            of_str = f" of {self.num_rounds}"
        while True:
            if not self.num_rounds == 1:
                await self.say(f"## {self.string_round(round+1).capitalize()}{of_str}:")
            await self.start_round()
            await self.core_game()
            await self.end_round()
            round += 1
            if round == self.num_rounds:
                break
