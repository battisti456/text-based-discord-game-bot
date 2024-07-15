#NEEDS TO BE TESTED
from math import ceil
from typing import override

from config.games_config import games_config
from game.components.game_interface import Game_Interface
from game.components.send.old_message import Old_Message
from game.game_bases import Card_Base, Elimination_Base
from utils.types import PlayerDict, PlayerId

HAND_LIMIT = games_config['elimination_blackjack']["hand_limit"]
NUM_PLAYERS_PER_DECK = games_config['elimination_blackjack']['num_players_per_deck']

class Elimination_Blackjack(Card_Base,Elimination_Base):
    def __init__(self,gi:Game_Interface):
        Card_Base.__init__(self,gi)
        Elimination_Base.__init__(self,gi)
    def player_points(self,player:PlayerId)->int:
        sum = 0
        num_aces = 0
        hand = self.hands[player]
        assert hand is not None
        for card in hand.cards:
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
    @override
    async def game_intro(self):
        await self.say(
            "# This will be a game of elimination blackjack!\n" +
            "We will play a round of blackjack, and, at the end, those with the lowest score are eliminated.\n" +
            "On your turn you may either choose to draw or pass. If you draw another card is added to your hand.\n" +
            "The point value of your hand is the sum of the number cards plus 10 for each face card.\n" +
            f"Aces are worth 11 points, unless that would put you over {HAND_LIMIT} in which case they are worth 1 point.\n" +
            f"If your score goes above {HAND_LIMIT}, you are immediately eliminated (earlier than if you had just scored lowest in the round).\n" +
            f"The closer to {HAND_LIMIT} you get, the higher the chance you will defeat your competitors, however.")
    @override
    async def core_round(self):
        await self.setup_cards(ceil(len(self.unkicked_players)/NUM_PLAYERS_PER_DECK))
        await self.player_draw(self.unkicked_players,2)
        players_passed:list[PlayerId] = []
        players_still_drawing = list(self.unkicked_players)
        while players_still_drawing:
            will_draw:PlayerDict[int] = await self.basic_no_yes("Will you draw another card?",players_still_drawing)
            players_who_drew:list[PlayerId] = list(player for player in will_draw if will_draw[player])
            players_passed += list(player for player in will_draw if not will_draw[player])
            await self.player_draw(players_who_drew,1)
            players_eliminated_this_draw:list[PlayerId] = list(player for player in players_who_drew if self.player_points(player) > HAND_LIMIT)
            if players_eliminated_this_draw:
                have_text = "have"
                if len(players_eliminated_this_draw) == 1:
                    have_text = "has"
                await self.say(f"{self.format_players_md(players_eliminated_this_draw)} {have_text} overdrawn.")
                await self.eliminate(players_eliminated_this_draw)
                if set(players_eliminated_this_draw) == set(self.not_eliminated):
                    return#restart the round
            players_still_drawing = list(player for player in self.unkicked_players if player not in players_passed)
        scores:dict[PlayerId,int] = {}
        for player in self.unkicked_players:
            player_score = self.player_points(player)
            hand = self.hands[player]
            assert hand is not None
            message = Old_Message(
                text = f"{self.format_players_md([player])} had a hand worth {player_score}.",
                attach_files=[self.ch_to_attachment(hand)]
            )
            await self.sender(message)
            scores[player] = player_score
        score_list:list[int] = list(set(scores[player] for player in scores))
        score_list.sort()
        low_score:int = score_list[0]
        await self.eliminate(list(player for player in self.unkicked_players if scores[player] == low_score))
        




        

