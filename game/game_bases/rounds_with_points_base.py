import game
from game import userid
from typing import Callable

class Rounds_With_Points_Base(game.Game):
    def __init__(self,gh:game.GH):
        game.Game.__init__(self,gh)
        if not Rounds_With_Points_Base in self.initialized_bases:
            self.initialized_bases.append(Rounds_With_Points_Base)
            self.points:dict[int,int] = {}
            for player in self.players:
                self.points[player] = 0
            self.num_rounds:int = 3
            self.points_format:Callable = lambda x: f"{x} points"
            self.round_name = "round"
            self.reverse_scoring = False
    @game.police_messaging
    async def score(self,player:int|list[int] = None, num:int|dict[userid,int] = None, mute:bool = False):
        n = self.make_player_dict(num)
        p = self.deduce_players(player,n)
        now_text:dict[userid,str] = self.make_player_dict("")
        if not num is None:
            for player in p:
                if not n[player] is None and not n[player] == 0:
                    self.points[player] += n[player]
                    now_text[player] = "now "
        if len(p) == 1 and not mute:
            await self.policed_send(f"{self.mention(p[0])} {now_text[p[0]]}has {self.points_format(self.points[p[0]])}.")
        elif self.allowed_to_speak() and not mute:
            frmt = list(f"{self.mention(player)} {now_text[player]}has {self.points_format(self.points[player])}" for player in p)
            if frmt:
                await self.send(game.wordify_iterable(frmt))
    @game.police_messaging
    async def run(self) -> list[userid|list[userid]]:
        await self.game_intro()
        await self.game_setup()
        for round in range(self.num_rounds):
            if self.num_rounds != 1:
                await self.policed_send(f"Now beggining {self.round_name} #{round+1} of {self.num_rounds}.")
            points_to_add:dict[userid,int] = await self.core_game()
            if points_to_add:
                await self.score(num=points_to_add)#announces score if core_game returned none, changes score if core_game returned values
        await self.game_cleanup()
        scores = list(set(self.points[player] for player in self.points))
        scores.sort()
        if not self.reverse_scoring:
            scores.reverse()
        rank:list[userid|list[userid]] = []
        for score in scores:
            players_at_score = list(player for player in self.players if self.points[player] == score)
            if len(players_at_score) == 1:
                rank.append(players_at_score[0])
            else:
                rank.append(players_at_score)
        await self.game_outro(rank)
        return rank
    async def game_setup(self):
        pass
    async def game_cleanup(self):
        pass
    async def game_intro(self):
        pass
    async def game_outro(self,rank:list[int]):
        pass
    async def core_game(self) -> list[int]|None:
        pass