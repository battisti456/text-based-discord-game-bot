import dataclasses
import random
from collections import Counter
from itertools import combinations
from typing import Annotated, override

import PIL.Image
import PIL.ImageOps
from color_tools_battisti456 import Color
from config_system_battisti456.config_item import Integer, Path, Ratio, Bool

import utils.emoji_groups
from config import Config
from game import make_player_dict
from game.components.game_interface import Game_Interface
from game.components.participant import Player, PlayerDict, mention_participants
from game.components.send import Address
from game.components.send.sendable.sendables import Text_With_Files
from game.game import Game
from utils.common import arg_fix_grouping
from utils.config_items import ColorConfigItem
from utils.grammar import temp_file_path, wordify_iterable
from utils.types import GS, Grouping


class config(Config):
    card_path:Annotated[str,Path(level=3)] = 'data/cards'
    card_width:Annotated[int,Integer(level=1,min_value=1)] = 300
    hand_width:Annotated[int,Integer(level=1,min_value=1)] = 1200
    hand_padding:Annotated[int,Integer(level=1,min_value=0)] = 20
    hand_color:Annotated[Color,ColorConfigItem(level=1)] = (0,0,0,0)
    overlap_ratio:Annotated[float,Ratio(level=1)] = 0.25
    better_art:Annotated[bool,Bool(level=1)] = True

POKER_HAND_NAMES = ["high card","pair","two pair","three of a kind","straight","flush","full house","four of a kind","straight flush","royal flush"]
SUIT_NAMES = ["spades","hearts","diamonds","clubs"]
CARD_NAMES = ["ace","two","three","four","five","six","seven","eight","nine","ten","jack","queen","king"]
CARD_JOIN = " "

#region card stuff
def card_file_name(suit:int,value:int):
    better_art = ""
    if ((value == 0 and suit == 0) or value > 9) and config.better_art:
        better_art = "2"
    card_text = CARD_NAMES[value]
    if value > 0 and value < 10:
        card_text = str(value +1)
    return f"{card_text}_of_{SUIT_NAMES[suit]}{better_art}.png"

def wordify_cards(cards:Grouping['Card']) -> str:
    return wordify_iterable(card.string() for card in cards)
def frequency(values:list[int]) -> dict[int,int]:
    return dict(Counter(values))

@dataclasses.dataclass(frozen=True)
class Card(GS):
    suit:int
    value:int
    def string(self)->str:
        return f"{CARD_NAMES[self.value].capitalize()} of {SUIT_NAMES[self.suit].capitalize()}"
    @override
    def __str__(self) -> str:
        return f"{type(self)}({self.string})"
    def emoji(self)->str:
        return utils.emoji_groups.PLAYING_CARD_EMOJI[self.suit*len(CARD_NAMES)+self.value]
    def image(self,card_width:int = config.card_width)->PIL.Image.Image:#doen't keep transparent corners....?
        image = PIL.Image.open(f"{config.card_path}/{card_file_name(self.suit,self.value)}")
        image = image.convert('RGBA')
        width,height = image.size
        return image.resize((card_width,int(height/width*card_width)))
    def card_num(self):
        return self.value+1
    def is_face(self):
        return self.value > 9
    @override
    def __hash__(self) -> int:
        return self.suit*4 + self.value
class Card_Holder(object):
    def __init__(self,name:str = ""):
        self.name = name
        self.cards:list[Card] = []
    def shuffle(self):
        random.shuffle(self.cards)
    def string_contents(self) -> str:
        return wordify_cards(self.cards)
    def emoji_contents(self) -> str:
        return CARD_JOIN.join(card.emoji() for card in self.cards)
    def image(self) -> PIL.Image.Image:
        effective_cards_at_max_overlap:float = ((len(self.cards)-1)*config.overlap_ratio + 1)
        card_width = config.card_width
        overlap_ratio = config.overlap_ratio
        offset = 0
        if effective_cards_at_max_overlap*config.card_width > config.hand_width:#there are too many cards, need to shrinkpl\
            card_width = int(config.hand_width/effective_cards_at_max_overlap)
        elif config.card_width*len(self.cards) < config.hand_width:#no overlap needed
            overlap_ratio = 1
            offset = (config.hand_width-config.card_width*len(self.cards))/2
        else:
            overlap_ratio = (config.hand_width/config.card_width-1)/(len(self.cards)-1)
        card_images:list[PIL.Image.Image] = list(card.image(card_width) for card in self.cards)
        if card_images:
            hand_height = card_images[0].size[1]
        else:#no cards
            hand_height = 80
        base = PIL.Image.new('RGBA',(config.hand_width,hand_height),color = config.hand_color)
        for i in range(len(self.cards)):
            base.paste(card_images[i],(int(offset+i*card_width*overlap_ratio),0),card_images[i])
        return PIL.ImageOps.expand(base,border = config.hand_padding,fill =config.hand_color)
    def give(self,other:'Card_Holder',num_random_cards:int = 0,cards:int|Card|Grouping[int]|Grouping[Card]= []) -> list[Card]:
        cards_to_remove:set[Card] = set()
        if isinstance(cards,int):
            cards_to_remove.add(self.cards[cards])
        elif isinstance(cards,Card):
            cards_to_remove.add(cards)
        else:
            for card in cards:
                if isinstance(card,int):
                    cards_to_remove.add(self.cards[card])
                else:
                    cards_to_remove.add(card)
        if num_random_cards + len(cards_to_remove) > len(self.cards):
            raise Exception(f"We cannot remove {num_random_cards+len(cards_to_remove)} from {len(self.cards)} cards")
        random_cards:set[Card] = set(random.sample(list(card for card in self.cards if card not in cards_to_remove), num_random_cards))
        cards_to_remove.update(random_cards)
        for card in cards_to_remove:
            self.cards.remove(card)
            other.cards.append(card)
        return list(cards_to_remove)
    def take(self,other:'Card_Holder',num_random_cards:int = 0,cards:int|Card|Grouping[int]|Grouping[Card]= []) -> Grouping[Card]:
        return other.give(self,num_random_cards,cards)

        

class Hand(Card_Holder):
    pass

class Deck(Card_Holder):
    def __init__(self,num = 1):
        Card_Holder.__init__(self)
        for n in range(num):
            for suit in range(len(SUIT_NAMES)):
                for value in range(len(CARD_NAMES)):
                    self.cards.append(Card(suit,value))
        self.shuffle()
class Poker_Hand(Card_Holder):
    def get_poker_values(self) -> list[int]:
        values = []
        for card in self.cards:
            if card.value == 0:#an ace
                values.append(13)
            else:
                values.append(card.value)
        return values
    def is_royal_flush(self) -> bool:
        values = self.get_poker_values()
        values.sort(reverse=True)
        return self.is_straight_flush() and values[0] == 13
    def is_straight_flush(self) -> bool:
        return self.is_flush() and self.is_straight()
    def is_four_of_a_kind(self) -> bool:
        values=  self.get_poker_values()
        for check_value in set(values):
            if sum(1 for value in values if value == check_value) >= 4:
                return True
        return False
    def is_full_house(self) -> bool:
        values = self.get_poker_values()
        totals:dict[int,int] = {}
        for value_check in set(values):
            totals[value_check] = sum(1 for value in values if value == value_check)
        desired = [2,3]
        for value_check in totals:
            if totals[value_check] in desired:
                desired.remove(totals[value_check])
            else:
                return False
        return len(desired) == 0
    def is_flush(self) -> bool:
        suits = list(card.suit for card in self.cards)
        return len(set(suits)) == 1
    def is_straight(self) -> bool:
        values = self.get_poker_values()
        values.sort()
        i=0
        while values[i+1] == values[i] +1:
            i += 1
            if i == len(values)-1:
                return True
        return False
    def is_three_of_a_kind(self) -> bool:
        values=  self.get_poker_values()
        for check_value in set(values):
            if sum(1 for value in values if value == check_value) >= 3:
                return True
        return False
    def is_two_pair(self) -> bool:
        values = self.get_poker_values()
        totals:dict[int,int] = {}
        for value_check in set(values):
            totals[value_check] = sum(1 for value in values if value == value_check)
        desired = [2,2]
        for value_check in totals:
            if totals[value_check] in desired:
                desired.remove(totals[value_check])
            else:
                return False
        return len(desired) == 0
    def is_pair(self) -> bool:
        #doesn't check for other hands
        values = self.get_poker_values()
        return len(set(values)) < len(values)
    def rank(self) -> int:
        hand_value = 0
        arranged_values =  []
        card_values = self.get_poker_values()

        def remove_by_freq(freq_num:int):
            freq = frequency(card_values)
            for value in freq:
                if freq[value] == freq_num:
                    for i in range(freq_num):
                        arranged_values.append(value)
                        card_values.remove(value)
                    return

        if self.is_royal_flush():#by high
            hand_value = 9
        elif self.is_straight_flush(): #by high
            hand_value = 8
        elif self.is_four_of_a_kind():# four than other
            hand_value = 7
            remove_by_freq(4)
        elif self.is_full_house():#three, then two
            hand_value = 6
            remove_by_freq(3)
        elif self.is_flush():#by high
            hand_value = 5
        elif self.is_straight():#by high
            hand_value = 4
        elif self.is_three_of_a_kind():#order three, then others by high
            hand_value = 3
            remove_by_freq(3)
        elif self.is_two_pair():#order high pair, low pair, other card
            hand_value = 2
            remove_by_freq(2)
            remove_by_freq(2)
            if arranged_values[0] < arranged_values[2]:
                low = arranged_values[0]
                arranged_values[0] = arranged_values[2]
                arranged_values[1] = arranged_values[2]
                arranged_values[2] = low
                arranged_values[3] = low
        elif self.is_pair():#order should be pair, then rest of cards by high
            hand_value = 1
            remove_by_freq(2)
        card_values.sort(reverse=True)
        values = [hand_value] + arranged_values + card_values
        values.reverse()
        total = 0
        for i in range(len(values)):
            total += values[i] * 16**i
        return total#each digit should be hand value, then descending order of cards in base 16

def best_poker_hand(*args:Card_Holder) -> tuple[Poker_Hand,int]:
    cards:list[Card] = []
    for arg in args:
        cards = cards + arg.cards
    test_poker_hand = Poker_Hand()
    found_poker_hand = Poker_Hand()
    found_rank = -1
    for card_set in combinations(cards,5):
        test_poker_hand.cards = list(card_set)
        test_rank = test_poker_hand.rank()
        if test_rank > found_rank:
            found_poker_hand.cards = list(card_set)
            found_rank = test_rank
    return found_poker_hand,found_rank

def name_poker_hand_by_rank(rank:int) -> str:
    hex_string = hex(rank)[2:]
    if len(hex_string) == 5:#first digit was zero
        hex_string = '0' + hex_string
    hand_int = int('0x' + hex_string[0], base = 16)
    return POKER_HAND_NAMES[hand_int]
#endregion

class Card_Base(Game):
    def __init__(self,gi:Game_Interface):
        Game.__init__(self,gi)
        if Card_Base not in self.initialized_bases:
            self.initialized_bases.append(Card_Base)
            self.hand_addresses:PlayerDict[Address|None] = make_player_dict(self.unkicked_players,None)
    async def setup_cards(self,num_decks:int = 1):
        self.deck:Deck = Deck(num_decks)
        self.discard = Card_Holder()
        self.hands:PlayerDict[Hand] = {}
        for player in self.unkicked_players:
            self.hands[player] = Hand()
        for player in self.unkicked_players:
            if self.hand_addresses[player] is None:#if first time
                address = await self.gi.default_sender.generate_address(player,player.name +"'s Hand")
                self.hand_addresses[player] = address
            await self.update_hand(player)
    def ch_to_attachment(self,ch:Card_Holder) -> str:
        image = ch.image()
        path = temp_file_path(".png")
        image.save(path)
        return path
    async def update_hand(self,player:Player,add_text:str = ""):
        contents = add_text
        hand = self.hands[player]
        assert hand is not None
        if self.allowed_to_speak():
            if contents != "":
                contents += "; "
            if self.hands[player]:
                contents += f"Your hand contains the {hand.string_contents()}"
            else:
                contents += "Your hand is empty."
        await self.sender(Text_With_Files(
            attach_files=(self.ch_to_attachment(hand),),
            text=contents
        ),self.hand_addresses[player])
    async def player_draw(self,player:Player|Grouping[Player],num:int = 1):
        players:Grouping[Player] = arg_fix_grouping(self.unkicked_players,player)
        if players:
            await self.say(f"{mention_participants(players)} drew {num} card(s).")
        for _player in players:
            hand:Hand|None = self.hands[_player]
            assert hand is not None
            cards = hand.take(self.deck,num)
            draw_text = ""
            if self.allowed_to_speak():
                draw_text = f"You drew: {wordify_cards(cards)}."
            await self.update_hand(_player,draw_text)
    async def player_discard(self,player:Player,num_random:int = 0,cards:int|Card|Grouping[int]|Grouping[Card] = []):
        hand = self.hands[player]
        assert hand is not None
        cards = hand.give(self.discard,num_random,cards)
        discard_text = ""
        await self.say(f"{mention_participants([player])} discarded {len(cards)} card(s).")
        if self.allowed_to_speak():
            discard_text = f"You discarded: {wordify_cards(cards)}."
        await self.update_hand(player,discard_text)
    async def shuffle_discord_into_deck(self):
        self.discard.give(self.deck,cards=self.deck.cards)
        self.deck.shuffle()
        await self.say("The discard has been shuffled back into the deck.")

    
        
        
