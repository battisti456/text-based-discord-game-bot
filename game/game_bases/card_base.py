import game
import game.emoji_groups
import random


import PIL.Image
import PIL.ImageOps
#import cairosvg broken?
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from io import BytesIO

svg2rlg()


from typing import Iterable

SUIT_NAMES = ["spades","hearts","diamonds","clubs"]
CARD_NAMES = ["ace","two","three","four","five","six","seven","eight","nine","ten","jack","queen","king"]
CARD_JOIN = " "
CARD_PATH = "data\\cards"
CARD_WIDTH = 200
HAND_WIDTH = 1600
HAND_PADDING = 20
HAND_COLOR = (0,0,0,0)
OVERLAP_RATIO = 0.25

def wordify_cards(cards:Iterable['Card']) -> str:
    return game.wordify_iterable(card.string() for card in cards)

class Card(object):
    def __init__(self,suit:int,value:int):
        self.suit = suit
        self.value = value
    def string(self)->str:
        return f"{CARD_NAMES[self.value].capitalize()} of {SUIT_NAMES[self.suit].capitalize()}"
    def emoji(self)->str:
        return game.emoji_groups.PLAYING_CARD_EMOJI[self.suit*len(CARD_NAMES)+self.value]
    def image(self,card_width:int = CARD_WIDTH)->PIL.Image.Image:
        out = BytesIO()
        path:str = CARD_PATH + "\\" + self.string() +".svg"
        with open(path,'r') as file:
            drawing = svg2rlg(file)
            bounds:tuple[int,int,int,int] = drawing.getBounds()
            scale = card_width/abs(bounds[0]-bounds[2])
            drawing.scale(scale,scale)
            renderPM.drawToFile(drawing,out,fmt='png')
            #cairosvg.svg2png(file_obj = file,write_to = out,output_width = card_width)
        return PIL.Image.open(out)
    def card_num(self):
        return self.value+1
    def is_face(self):
        return self.value > 9
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
        effective_cards_at_max_overlap = ((len(self.cards)-1)*OVERLAP_RATIO + 1)
        card_width = CARD_WIDTH
        overlap_ratio = OVERLAP_RATIO
        offset = 0
        if effective_cards_at_max_overlap*CARD_WIDTH > HAND_WIDTH:#there are too many cards, need to shrink
            card_width = HAND_WIDTH/effective_cards_at_max_overlap
        elif CARD_WIDTH*len(self.cards) < HAND_WIDTH:#no overlap needed
            overlap_ratio = 1
            offset = (HAND_WIDTH-CARD_WIDTH*len(self.cards))/2
        else:
            overlap_ratio = (HAND_WIDTH/CARD_WIDTH-1)/(len(self.hand)-1)
        card_images:list[PIL.Image.Image] = list(card.image(card_width) for card in self.cards)
        if card_images:
            hand_height = card_images[0].size[1]
        else:#no cards
            hand_height = 80
        base = PIL.Image.new('RGBA',(HAND_WIDTH,hand_height),color = HAND_COLOR)
        for i in range(len(self.cards)):
            base.paste(card_images[i],(int(offset+i*card_width*overlap_ratio),0))
        return PIL.ImageOps.expand(base,border = HAND_PADDING,fill =HAND_COLOR)
    def give(self,other:'Card_Holder',num_random_cards:int = 0,cards:int|Card|Iterable[int|Card]= []) -> Iterable[Card]:
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
        for i in range(num_random_cards):
            added = False
            while not added:
                card = random.choice(self.cards)
                if not card in cards_to_remove:
                    cards_to_remove.add(card)
                    added = True
        for card in cards_to_remove:
            self.cards.remove(card)
            other.cards.append(card)
        return cards_to_remove
    def take(self,other:'Card_Holder',num_random_cards:int = 0,cards:int|Card|Iterable[int|Card]= []) -> Iterable[Card]:
        return other.give(self,num_random_cards,cards)

        
        

class Hand(Card_Holder):
    pass

class Deck(Card_Holder):
    def __init__(self,name:str = ""):
        Card_Holder.__init__(self,name)
        for suit in range(len(SUIT_NAMES)):
            for value in range(len(CARD_NAMES)):
                self.cards.append(Card(suit,value))
        self.shuffle()
        

class Card_Base(game.Game):
    def __init__(self,gh:game.GH):
        game.Game.__init__(self,gh)
        self.hand_threads:dict[int,int] = {}
        self.hand_message:dict[int,int] = {}
    async def setup_cards(self):
        self.deck:Deck = Deck()
        self.discard = Card_Holder()
        self.hands:dict[int,Hand] = {}
        for player in self.players:
            self.hands[player] = Hand()
        for player in self.players:
            if not player in self.hand_threads:#if first time
                thread_id = await self.create_thread("Your hand")
                await self.invite_to_thread(thread_id,player)
                self.hand_threads[player] = thread_id
            await self.update_hand(player)
    async def send_ch(self,ch:Card_Holder,message:str = "",thread_id:int|None = None,message_id:int|None = None):
        image = ch.image()
        path = self.temp_file_path(".png")
        image.save(path)
        await self.send(content = message,attatchements_data=path,channel_id = thread_id,message_id = message_id)
    @game.police_messaging
    async def update_hand(self,player:int,message:str = ""):
        message_id = None
        if player in self.hand_message:
            message_id = self.hand_message[player]
        contents = message
        if self.allowed_to_speak():
            if contents != "":
                contents += "; "
            if self.hands[player]:
                contents += f"Your hand contains the {self.hands[player].string_contents()}"
            else:
                contents += "Your hand is empty."
        message_id = await self.send_ch(self.hands[player],contents,self.hand_threads[player],message_id)
        self.hand_message[player] = message_id
    @game.police_messaging
    async def player_draw(self,player:int|Iterable[int],num:int = 1):
        if isinstance(player,int):
            players = [player]
        else:
            players=player
        for player in players:
            cards = self.hands[player].take(self.deck,num)
            draw_text = ""
            await self.policed_send(f"{self.mention(player)} drew {len(cards)} card(s).")
            if self.allowed_to_speak():
                draw_text = f"You drew: {wordify_cards(cards)}"
            await self.update_hand(player,draw_text)
    @game.police_messaging
    async def player_discard(self,player:int,num_random:int = 0,cards:int|Card|Iterable[int]|Iterable[Card] = []):
        cards = self.hands[player].give(self.discard,num_random,cards)
        discard_text = ""
        await self.policed_send(f"{self.mention(player)} discarded {len(cards)} card(s).")
        if self.allowed_to_speak():
            discard_text = f"You discarded: {wordify_cards(cards)}."
        await self.update_hand(player,discard_text)
    @game.police_messaging#wildly untested....
    async def shuffle_discord_into_deck(self):
        self.discard.give(self.deck,cards=self.deck.cards)
        self.deck.shuffle()
        self.policed_send("The discard has been shuffled back into the deck.")

    
        
        
