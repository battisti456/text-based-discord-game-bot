import game
from game.game_bases import Card_Base
from game.game_bases import Elimination_Base

from math import ceil

from typing import Iterable
from game import PlayerId

HAND_LIMIT = 21
NUM_PLAYERS_PER_DECK = 7

class Elimination_Blackjack(Card_Base,Elimination_Base):
    def __init__(self,gh:game.GH):
        Card_Base.__init__(self,gh)
        Elimination_Base.__init__(self,gh)
    def player_points(self,player:int)->int:
        sum = 0
        num_aces = 0
        for card in self.hands[player].cards:
            if card.is_face():
                sum += 10
            else:
                num = card.card_num()
                sum += num
                if num == 1:#card is an ace
                    num_aces += 1
        while num_aces > 0 and sum + 10 < HAND_LIMIT:
            sum += 10
            num_aces -= 1
        return sum
    async def game_intro(self):
        await self.basic_send(
            "# This will be a game of elimination blackjack!\n" +
            "We will play a round of blackjack, and, at the end, those with the lowest score are eliminated.\n" +
            "On your turn you may either choose to draw or pass. If you draw another card is added to your hand.\n" +
            "The point value of your hand is the sum of the number cards plus 10 for each face card.\n" +
            f"Aces are worth 11 points, unless that would put you over {HAND_LIMIT} in which case they are worth 1 point.\n" +
            f"If your score goes above {HAND_LIMIT}, you are immediately eliminated (earlier than if you had just scored lowest in the round).\n" +
            f"The closer to {HAND_LIMIT} you get, the higher the chance you will defeat your competitors, however.")
    async def game_outro(self,order:Iterable[int]):
        pass
    async def core_game(self,remaining_players:list[int])->[int]:
        await self.setup_cards(ceil(len(remaining_players)/NUM_PLAYERS_PER_DECK))
        await self.player_draw(remaining_players,2)
        players_passed:list[int] = []
        players_still_drawing = remaining_players.copy()
        while players_still_drawing:
            will_draw:dict[PlayerId,int] = await self.basic_no_yes(f"Will you draw another card?",players_still_drawing)
            players_who_drew:list[PlayerId] = list(player for player in will_draw if will_draw[player])
            players_passed += list(player for player in will_draw if not will_draw[player])
            await self.player_draw(
                players_who_drew,1,
                lambda player:f"Your hand has a score of {self.player_points(player)}.")
            players_eliminated_this_draw:list[PlayerId] = list(player for player in players_who_drew if self.player_points(player) > HAND_LIMIT)
            if players_eliminated_this_draw:
                have_text = "have"
                if len(players_eliminated_this_draw) == 1:
                    have_text = "has"
                await self.basic_send(f"{self.format_players_md(players_eliminated_this_draw)} {have_text} overdrawn.")
                exit_core = await self.eliminate_players(players_eliminated_this_draw)
                if exit_core:
                    return
            players_still_drawing = list(player for player in self.get_remaining_players() if not player in players_passed)
        remaining_players = self.get_remaining_players()
        scores:dict[PlayerId,int] = {}
        for player in remaining_players:
            player_score = self.player_points(player)
            await self.send_ch(self.hands[player],f"{self.format_players_md(player)} had a hand worth {player_score}.")
            scores[player] = player_score
        score_list:list[int] = list(set(scores[player] for player in scores))
        score_list.sort()
        low_score:int = score_list[0]
        return list(player for player in remaining_players if scores[player] == low_score)
        




        

