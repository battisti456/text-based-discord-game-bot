import game
from game import userid
from typing import Iterable

import game_handler

class Elimination_Base(game.Game):
    def __init__(self,gh:game_handler.Game_Handler):
        game.Game.__init__(self,gh)
    @game.police_messaging
    async def run(self) -> list[userid|list[userid]]:
        await self.game_intro()
        players_eliminated:list[userid|list[userid]] = []
        while len(self.players) - game.one_depth_len(players_eliminated) > 1:
            flat_eliminated = game.one_depth_flat(players_eliminated)
            players_to_be_eliminated = await self.core_game(list(player for player in self.players if not player in flat_eliminated))
            if isinstance(players_to_be_eliminated,int):
                players_eliminated.append(players_to_be_eliminated)
                await self.policed_send(f"{self.mention(players_to_be_eliminated)} was eliminated.")
            elif len(players_to_be_eliminated) + len(flat_eliminated) < len(self.players):
                if len(players_to_be_eliminated) == 0:
                    await self.policed_send(f"No one was eliminated.")
                elif len(players_to_be_eliminated) == 1:
                    players_eliminated.append(players_to_be_eliminated[0])
                    await self.policed_send(f"{self.mention(players_to_be_eliminated)} was eliminated.")
                else:
                    await self.policed_send(f"{self.mention(players_to_be_eliminated)} were eliminated.")
                    players_eliminated.append(players_to_be_eliminated)
            else:
                await self.policed_send(f"{self.mention(players_to_be_eliminated)} despite otherwise being eliminated, will continue to another round to narrow down a winner.")
        flat_eliminated = game.one_depth_flat(players_eliminated)
        winner = next(player for player in self.players if not player in flat_eliminated)
        await self.policed_send(f"{self.mention(winner)} has won!")
        players_eliminated.append(winner)
        players_eliminated.reverse()
        await self.game_outro(players_eliminated)
        return players_eliminated
    async def game_intro(self):
        pass
    async def game_outro(self,order:Iterable[int]):
        pass
    async def core_game(self,remaining_players:Iterable[int])->[int]:
        pass