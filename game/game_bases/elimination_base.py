from game import PlayerId, PlayerDict, PlayerPlacement
from game.game_interface import Game_Interface
from game.game import Game, police_game_callable

class Elimination_Base(Game):
    def __init__(self,gi:Game_Interface):
        Game.__init__(self,gi)
        if not Elimination_Base in self.initialized_bases:
            self.initialized_bases.append(Elimination_Base)
            self.players_eliminated:PlayerPlacement = []

    @police_game_callable
    async def eliminate_players(self,players:PlayerId|list[PlayerId]):
        """
        eliminates players unless this would eliminate all remaining players, then it does not eliminate the players
        """
        if isinstance(players,int):
            players = [players]
        if players:
            assert isinstance(players,list)
            if len(players) == len(self.unkicked_players):
                await self.basic_policed_send(f"{self.format_players_md(players)} despite otherwise being eliminated will continue to another round.")
            else:
                await self.kick_players(players,'eliminated')
    @police_game_callable
    async def _run(self):
        while len(self.unkicked_players) >= 2:
            await self.core_game()
    async def core_game(self):
        ...
    async def generate_placements(self) -> PlayerPlacement:
        return self.generate_kicked_placements()