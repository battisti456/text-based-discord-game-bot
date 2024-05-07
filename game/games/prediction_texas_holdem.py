from config.games_config import games_config

from game.components.game_interface import Game_Interface
from game.game_bases import Rounds_With_Points_Base, Card_Base

from game.game_bases.card_base import Card_Holder,best_poker_hand, Poker_Hand, name_poker_hand_by_rank
from game.utils.emoji_groups import NUMBERED_KEYCAP_EMOJI
from game.utils.grammer import ordinate

from game import PlayerId, PlayerDict, make_player_dict

CONFIG = games_config['prediction_texas_holdem']

NUM_ROUNDS = CONFIG['num_rounds']

PLAYER_CARDS = CONFIG['player_cards']
SHARED_CARDS = CONFIG['shared_cards']

class Prediction_Texas_Holdem(Rounds_With_Points_Base,Card_Base):
    def __init__(self,gi:Game_Interface):
        Rounds_With_Points_Base.__init__(self,gi)
        Card_Base.__init__(self,gi)
        self.reverse_scoring = True
        self.points_format = lambda points: f"{points} penalties"
        self.num_rounds = NUM_ROUNDS
    async def game_intro(self):
        await self.basic_send(
            "# Welcome to a game of prediction Texas Holdem!\n" +
            "This isn't going to work like most games of Texas Holdem.\n" +
            f"In this game, you get {PLAYER_CARDS} to yourself while there are {SHARED_CARDS} shared.\n" +
            "You must then predict (solely based on what cards you have) what your best poker hand's rank would be against the other player's best hands.\n" +
            "Best poker hands are constructed from a combination of your private hand and the shared cards.\n" +
            "The further you are from guessing your rank correctly, the more penalties you accrue.\n" +
            "Lowest penalties at the end of the game wins!"
        )
    async def core_game(self) -> PlayerDict[int] | None:
        await self.setup_cards()
        shared:Card_Holder = Card_Holder("Shared cards.")
        await self.player_draw(self.unkicked_players,PLAYER_CARDS)
        self.deck.give(shared,SHARED_CARDS)
        attachment = self.ch_to_attachment(shared)
        await self.basic_send(
            "Here are the shared cards:",
            attatchements_data=[attachment]
        )
        responses = await self.basic_multiple_choice(
            "Judging from your own cards and the shared cards, where do you think you will place amongst your fellow players?",
            list(ordinate(num+1) for num in range(len(self.unkicked_players))),
            self.unkicked_players,
            list(NUMBERED_KEYCAP_EMOJI[1:])
        )
        players_best_poker_hands:dict[PlayerId,Poker_Hand] = dict()
        player_hand_ranks:dict[PlayerId,int] = dict()
        for player in self.unkicked_players:
            players_best_poker_hands[player],player_hand_ranks[player] = best_poker_hand(self.hands[player],shared)
        ranking=list(self.unkicked_players)
        ranking.sort(key = lambda player: player_hand_ranks[player],reverse=True)
        sorted_ranks = list(player_hand_ranks[player] for player in self.unkicked_players)
        sorted_ranks.sort(reverse=True)
        player_diffs:PlayerDict[int] = make_player_dict(self.unkicked_players,0)
        for player in self.unkicked_players:
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
                    down_check = False
            player_diffs[player] = diff
        for player in self.unkicked_players:
            await self.basic_send(
                f"{self.format_players_md([player])}'s hand was:",
                [self.ch_to_attachment(self.hands[player])]
            )
            await self.basic_send(
                f"Meaning {self.format_players_md([player])}'s best poker hand with the shared cards was:",
                [self.ch_to_attachment(players_best_poker_hands[player])]
            )
            await self.basic_send(
                f"This placed {self.format_players_md([player])} {ordinate(1+ranking.index(player))} "+
                f"in the hand rankings with a {name_poker_hand_by_rank(player_hand_ranks[player])}, "+
                f"and they predicted they would be {ordinate(responses[player]+1)}."
            )
        await self.score(self.unkicked_players,player_diffs)