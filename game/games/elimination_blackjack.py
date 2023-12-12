import game
from game.game_bases import Card_Base
from game.game_bases import Elimination_Base

from typing import Iterable

class Elimination_Blackjack(Card_Base,Elimination_Base):
    def __init__(self,gh:game.GH):
        Card_Base.__init__(self,gh)
        Elimination_Base.__init__(self,gh)
    def player_points(self,player:int)->int:
        sum = 0
        for card in self.hands[player].cards:
            if card.is_face():
                sum += 10
            else:
                sum += card.card_num()
        return sum
    async def game_intro(self):
        await self.send(
            """# This will be a game of elimination blackjack.
            We will play a round of blackjack, and, if there is a tie, the highest scores will compete in another round.
            On your turn you may either choose to draw or pass. If you draw another card is added to your hand.
            The point value of your hand is the sum of the number cards plus 10 for each face card.
            If your score goes above 21, you lose.
            The closer to 21 you get, the higher the chance you will defeat your competitors.
            Becaus the highest point value after everyone has passed wins the round!""")
    async def game_outro(order:Iterable[int]):
        pass
    async def core_game(self,remaining_players:Iterable[int])->[int]:
        await self.setup_cards()
        await self.player_draw(remaining_players)
        players_passed:list[int] = []
        players_eliminated:list[int] = []
        while len(players_passed) + len(players_eliminated) < len(remaining_players):
            for player in (player for player in remaining_players if not (player in players_passed or player in players_eliminated)):
                will_draw = await self.no_yes(f"{self.mention(player)}, will you draw another card?",player)
                if will_draw:
                    await self.player_draw(player)
                    if self.player_points(player) > 21:
                        await self.send(f"{self.mention(player)} has overdrawn.")
                        players_eliminated.append(player)
                else:
                    await self.send(f"{self.mention(player)} has chosen to stay with their current cards.")
                    players_passed.append(player)
        if len(players_passed) <= 1:#no players remaining or one player remaining
            return players_eliminated
        scores:list[int] = []
        for player in players_passed:
            player_score = self.player_points(player)
            await self.send_ch(self.hands[player],f"{self.mention(player)} had {player_score}.")
            scores.append(player_score)
        sorted_scores = list(set(scores)).sort()
        for value in sorted_scores[:-1]:
            for i in range(len(scores)):
                if scores[i] == value:
                    players_eliminated.append(players_passed[i])
        return players_eliminated




        

