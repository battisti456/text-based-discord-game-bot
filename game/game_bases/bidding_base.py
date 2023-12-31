import game
from game import PlayerId, MessageId, ChannelId

from typing import Callable

ACCEPT_EMOJI = "👌"

def moneyfy(value:int):
    to_return = ""
    if value < 0:
        to_return += "-"
    to_return += "$" + str(abs(value))
    return to_return

class Bidding_Base(game.Game):
    def __init__(self,gh:game.GH):
        game.Game.__init__(self,gh)
        if not Bidding_Base in self.initialized_bases:
            self.initialized_bases.append(Bidding_Base)
            self.min_bid:int = 1
            self.bid_unit_function:Callable[[int],str] = moneyfy
    async def get_bid(self,players:list[PlayerId],starting_bid:int,bid_thread_id:ChannelId = None) -> tuple[PlayerId,int]:
        highest_bid:tuple[PlayerId,int] = (None,starting_bid)
        players_done:dict[PlayerId,bool] = self.make_player_dict(False,players)
        def generate_text() -> str:
            text = f"Let's bid! Please react to this message with {ACCEPT_EMOJI} to signal you are done bidding."
            if highest_bid[0] is None:
                text += f"\nBid {self.bid_unit_function(highest_bid[1])} to start the bidding."
            else:
                text += f"\n{self.format_players_md(highest_bid[0])} has the highest bid at {self.bid_unit_function(highest_bid[1])}."
                if self.min_bid > 1:
                    text += f"\nRemember, you must exceed the previous bid by at least {self.min_bid} to place a new one."
        message_id:MessageId = await self.basic_send(generate_text(),channel_id=bid_thread_id)
        async def on_reaction(emoji:str,player:PlayerId):
            if emoji == ACCEPT_EMOJI and player in players:
                players_done[player] = True
        async def on_message(message:str,player:PlayerId):
            if player in players:
                if message.isdigit():
                    if int(message) >= highest_bid[1] + self.min_bid or highest_bid[0] == None and int(message) >= highest_bid[1]:
                        highest_bid = (player,int(message))
                        await self.basic_send(generate_text(),channel_id=bid_thread_id,message_id=message_id)         
        self.add_reaction_action(on_reaction)
        self.add_message_action(on_message)
        await self.gi.add_reaction(ACCEPT_EMOJI,message_id)
        while not all(players_done[player] for player in players):
            await self.wait(game.CHECK_TIME)
        if highest_bid[0] is None:
            return None
        else:
            return highest_bid
