import game 
from game.game import Game, police_game_callable
from game.game_interface import Game_Interface
from game.message import Message
from game.grammer import wordify_iterable
from game import PlayerId, PlayerDict, make_player_dict, correct_int, PlayerPlacement
from typing import Callable, Optional

class Rounds_With_Points_Base(Game):
    def __init__(self,gi:Game_Interface):
        Game.__init__(self,gi)
        if not Rounds_With_Points_Base in self.initialized_bases:
            self.initialized_bases.append(Rounds_With_Points_Base)
            self.points:PlayerDict[int] = {}
            for player in self.players:
                self.points[player] = 0
            self.num_rounds:int = 3
            self.points_format:Callable = lambda x: f"{x} points"
            self.round_name = "round"
            self.reverse_scoring = False
    @police_game_callable
    async def score(self,player:Optional[PlayerId|list[PlayerId]], num:int|PlayerDict[int], mute:bool = False):
        p:list[PlayerId] = []
        if isinstance(player,int):
            p.append(player)
        elif isinstance(player,list):
            p += player
        n:PlayerDict[int] = {}
        if isinstance(num,int):
            n = make_player_dict(p,num)
        else:
            for ps in num:
                if not ps in p:
                    p.append(ps)
            n = num
        if p:
            await self._score(p,n,mute)
    @police_game_callable
    async def _score(self,players:list[PlayerId],num:PlayerDict[int], mute:bool):
        players_who_changed_score:list[PlayerId] = []
        for player in players:
            old_points:int|None = self.points[player] 
            new_points:int|None = num[player]
            if old_points is None:
                old_points = 0
            if new_points is None:
                new_points = 0
            self.points[player] = old_points + new_points
            if new_points != 0:
                players_who_changed_score.append(player)
        if mute or not players_who_changed_score:
            return
        await self.policed_send(Message(
            wordify_iterable(f"{self.sender.format_players_md([player])} now has {self.points_format(self.points[player])}" for player in players_who_changed_score)
        ))

    @police_game_callable
    async def run(self) -> PlayerPlacement:
        await self.game_intro()
        await self.game_setup()
        for round in range(self.num_rounds):
            if self.num_rounds != 1:
                await self.basic_policed_send(f"Now beggining {self.round_name} #{round+1} of {self.num_rounds}.")
            points_to_add:PlayerDict[int]|None = await self.core_game()
            if not points_to_add is None:
                await self.score(None,num=points_to_add)#announces score if core_game returned none, changes score if core_game returned values
        await self.game_cleanup()
        scores:list[int] = list(set(correct_int(self.points[player]) for player in self.points))
        scores.sort()
        if not self.reverse_scoring:
            scores.reverse()
        rank:PlayerPlacement = []
        for score in scores:
            players_at_score = list(player for player in self.players if self.points[player] == score)
            rank.append(players_at_score)
        await self.game_outro(rank)
        return rank
    async def game_setup(self):
        pass
    async def game_cleanup(self):
        pass
    async def game_intro(self):
        pass
    async def game_outro(self,rank:PlayerPlacement):
        pass
    async def core_game(self) -> PlayerDict[int] | None:
        pass