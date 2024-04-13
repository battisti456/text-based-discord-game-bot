import game
from game import PlayerId, PlayerDict, PlayerPlacement
from game.game_interface import Game_Interface
from game.game import Game, police_game_callable
from typing import Iterable

class Elimination_Base(Game):
    def __init__(self,gi:Game_Interface):
        Game.__init__(self,gi)
        if not Elimination_Base in self.initialized_bases:
            self.initialized_bases.append(Elimination_Base)
            self.players_eliminated:PlayerPlacement = []

    @police_game_callable
    async def eliminate_players(self,players:PlayerId|list[PlayerId]) -> bool:
        """Returns True to tell core_game that another round should be started after calling this.
        Either because all players would have been eliminated, or because someone won."""
        if isinstance(players,int):
            players = [players]
        if players:
            assert isinstance(players,list)
            if len(players) == len(self.unkicked_players) - self.get_num_eliminated():
                await self.basic_policed_send(f"{self.format_players_md(players)} despite otherwise being eliminated will continue to another round.")
                return True#all players would have been eliminated, restart round
            self.players_eliminated.append(players)
            were_text = "were"
            if len(players) == 1:
                were_text = "was"
            await self.basic_policed_send(f"{self.format_players_md(players)} {were_text} eliminated.")
            if self.get_num_eliminated() == len(self.unkicked_players) -1 :
                return True #winner decided
        return False #nothing happens
    def player_is_eliminated(self,player:PlayerId) -> bool:
        not_eliminated = True
        for elimination in self.players_eliminated:
            if isinstance(elimination,int):
                not_eliminated = not_eliminated and elimination != player
            else:
                not_eliminated = not_eliminated and not (player in elimination)
        return not not_eliminated
    def get_remaining_players(self) -> list[PlayerId]:
        return list(player for player in self.unkicked_players if not self.player_is_eliminated(player))
    def get_num_eliminated(self) -> int:
        num = 0
        for elimination in self.players_eliminated:
            if isinstance(elimination,int):
                num += 1
            else:
                num += len(elimination)
        return num
    @police_game_callable
    async def _run(self) -> PlayerPlacement:
        await self.game_intro()
        await self.game_setup()
        while self.get_num_eliminated() < len(self.unkicked_players) - 1:
            players_to_be_eliminated = await self.core_game(self.get_remaining_players())
            await self.eliminate_players(players_to_be_eliminated)
        await self.game_cleanup()
        players_left = self.get_remaining_players()
        assert len(players_left) == 1
        winner = players_left[0]
        await self.basic_policed_send(f"{self.format_players_md([winner])} has won!")
        self.players_eliminated.append([winner])
        self.players_eliminated.reverse()
        await self.game_outro(self.players_eliminated)
        return self.players_eliminated
    async def game_setup(self):
        pass
    async def game_cleanup(self):
        pass
    async def game_intro(self):
        pass
    async def game_outro(self,order:PlayerPlacement):
        pass
    async def core_game(self,remaining_players:Iterable[PlayerId])->list[PlayerId] | PlayerId:
        return []