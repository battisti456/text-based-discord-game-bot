from typing import Any, Coroutine
import game
from game.game_bases import Rounds_With_Points_Base, Card_Base

from game.game_bases.card_base import Card_Holder,best_poker_hand, Poker_Hand, name_poker_hand_by_rank
from game.emoji_groups import NUMBERED_KEYCAP_EMOJI

from game import userid

NUM_ROUNDS = 3

PLAYER_CARDS = 2
SHARED_CARDS = 5

class Prediction_Texas_Holdem(Rounds_With_Points_Base,Card_Base):
    def __init__(self,gh:game.GH):
        Rounds_With_Points_Base.__init__(self,gh)
        Card_Base.__init__(self,gh)
        self.reverse_scoring = True
        self.points_format = lambda points: f"{points} penalties"
        self.num_rounds = NUM_ROUNDS
    async def game_intro(self):
        await self.send(
            "# Welcome to a game of prediction Texas Holdem!\n" +
            "This isn't going to work like most games of Texas Holdem.\n" +
            f"In this game, you get {PLAYER_CARDS} to yourself while there are {SHARED_CARDS} shared.\n" +
            "You must then predict (solely based on what cards you have) what your best poker hand's rank would be against the other player's best hands.\n" +
            "Best poker hands are constructed from a combination of your private hand and the shared cards.\n" +
            "The further you are from guessing your rank correctly, the more penalties you accrue.\n" +
            "Lowest penalties at the end of the game wins!"
        )
    async def core_game(self) -> list[userid]:
        await self.setup_cards()
        shared:Card_Holder = Card_Holder("Shared cards.")
        await self.player_draw(self.players,PLAYER_CARDS)
        self.deck.give(shared,SHARED_CARDS)
        await self.send_ch(shared,"Here are the shared cards.")
        responses = await self.multiple_choice(
            "Judging from your own cards and the shared cards, where do you think you will place amongst your fellow players?",
            list(game.ordinate(num+1) for num in range(len(self.players))),
            self.players,
            NUMBERED_KEYCAP_EMOJI[1:]
        )
        players_best_poker_hands:dict[userid,Poker_Hand] = dict()
        player_hand_ranks:dict[userid,int] = dict()
        for player in self.players:
            players_best_poker_hands[player],player_hand_ranks[player] = best_poker_hand(self.hands[player],shared)
        ranking=list(self.players)
        ranking.sort(key = lambda player: player_hand_ranks[player],reverse=True)
        sorted_ranks = list(player_hand_ranks[player] for player in self.players)
        sorted_ranks.sort(reverse=True)
        player_diffs:dict[userid,int] = self.make_player_dict(0)
        for player in self.players:
            diff = -1
            up_check = False
            down_check = False
            while not (up_check or down_check):
                diff += 1
                if responses[player]+diff < len(sorted_ranks):
                    up_check = sorted_ranks[responses[player]+diff] == player_hand_ranks[player]
                else:
                    up_check = False
                if responses[player] - diff >= 0:
                    down_check = sorted_ranks[responses[player]-diff] == player_hand_ranks[player]
                else:
                    down_check - False
            player_diffs[player] = diff
        for player in self.players:
            await self.send_ch(
                self.hands[player],
                f"{self.mention(player)}'s hand was:"
            )
            await self.send_ch(
                players_best_poker_hands[player],
                f"Meaning {self.mention(player)}'s best poker hand with the shared cards was:"
            )
            await self.send(
                f"This placed {self.mention(player)} {game.ordinate(1+ranking.index(player))} "+
                f"in the hand rankings with a {name_poker_hand_by_rank(player_hand_ranks[player])}, "+
                f"and they predicted they would be {game.ordinate(responses[player]+1)}."
            )
        await self.score(self.players,player_diffs)