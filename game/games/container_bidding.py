import game
from typing import TypedDict
from game import userid
from game.game_bases import Rounds_With_Points_Base, Secret_Message_Base, Bidding_Base
import json
import random
import logging

NUM_CONTAINERS = 10
PATH = "container_contents.json"
STARTING_MONEY = 500
PERCENTILE_VAR = 10
END_OF_GAME_INTEREST = 20

class DescDict(TypedDict):
    starting_bid_range:tuple[int,int]
    num_items_range:tuple[int,int]
    possible_item_tiers:dict[str,int]
class DataDict(TypedDict):
    container_descriptions:dict[str,DescDict]
    container_types:dict[str,dict[str,int]]
    items:dict[str,int]

def moneyfy(value:int):
    to_return = ""
    if value < 0:
        to_return += "-"
    to_return += "$" + str(abs(value))
    return to_return

def validate_data(data:DataDict,logger:logging.Logger):
    for desc_text in data["container_descriptions"]:
        for tier_text in data["container_descriptions"][desc_text]["possible_item_tiers"]:
            if not tier_text in data["container_types"]:
                logger.error(f"In container data tier '{tier_text}' from desc '{desc_text}' is undefined.")
    for tier in data["container_types"]:
        for item in data["container_types"][tier]:
            if not item in data["items"]:
                logger.error(f"In container data item '{item}' from tier '{tier}'is undefined.")

class Container_Bidding(Rounds_With_Points_Base,Secret_Message_Base):
    def __init__(self,gh:game.GH):
        Rounds_With_Points_Base.__init__(self,gh)
        Secret_Message_Base.__init__(self,gh)
        self.num_rounds = NUM_CONTAINERS
        self.round_name = "bidding on container"
        self.points_format = lambda x: f"{moneyfy(x)} of valuables"
        with open(f"{self.config['data_path']}//{PATH}",'r') as file:
            self.data:DataDict = json.load(file)
        validate_data(self.data,self.logger)
        self.money = self.make_player_dict(STARTING_MONEY)
    async def game_intro(self):
        await self.send(f"""# Welcome to a game of container bidding!
                        In this game we will have {NUM_CONTAINERS} that we look at.
                        For each container my exper evaluator will prode their decription.
                        Then you must each secretly choose how much you would be willing to offer for it!
                        Afterwards, We will look through the container, evaluating the value of objects as we go and adding them to the score of the winning bidder.
                        You may always pay as much money as you would like for containers, but if you go past our starting cash of {moneyfy(STARTING_MONEY)},
                        then you will lose an extra {END_OF_GAME_INTEREST}% at the end of the game for interest.""")
    async def core_game(self):
        desc_name:str = random.choice(list(self.data["container_descriptions"]))
        desc:DescDict = self.data['container_descriptions'][desc_name]
        starting_bid:int = random.randint(desc["starting_bid_range"][0],desc["starting_bid_range"][1])
        question_text:str = f"Our expert evaluator described this container as '{desc_name}'.\nThe base bid is {moneyfy(starting_bid)}. How much are you willing to pay?"
        await self.send(f"{question_text}\nPlease respond in your private channel.")
        individual_message:dict[userid,str] = {}
        for player in self.players:
            individual_message[player] = f"{question_text}\nYou currently have {moneyfy(self.money[player])} available to bid."
        responses = await self.secret_text_response(self.players,individual_message)
        player_bids:dict[userid,int] = self.make_player_dict(0)
        for player in self.players:
            response:str = responses[player]
            response_only_num:str = "".join(list(num for num in response if num.isdigit()))
            if response_only_num != "":
                player_bids[player] = int(response_only_num)
        winning_players:list[userid] = []
        winning_bid:int = 0
        for player in self.players:
            if player_bids[player] == winning_bid:
                winning_players.append(player)
            elif player_bids[player] > winning_bid:
                winning_players = [player]
                winning_bid = player_bids[player]
        if winning_bid < starting_bid:
            await self.send("I see this container didn't quite pique your interests. Ah well.")
            return
        link_text = "won alone with a bid of"
        if len(winning_players) > 1:
            link_text = "tied and will split with bids of"
        await self.send(f"{self.mention(winning_players)} {link_text} {moneyfy(winning_bid)}.")
        total_reward:int = 0
        tier = random.choices(list(desc["possible_item_tiers"]),list(desc["possible_item_tiers"][tier] for tier in desc["possible_item_tiers"]))[0]
        num_items = random.randint(desc["num_items_range"][0],desc["num_items_range"][1])
        reward_text:list[str] = [f"When we open the container we discover that it's actually {tier}.\nThere are {num_items} items:"]
        item_dict:dict[str,int] = self.data["container_types"][tier]
        items = random.choices(list(item_dict),list(item_dict[item] for item in item_dict),k = num_items)
        for item in items:
            var = random.randint(100-PERCENTILE_VAR,100+PERCENTILE_VAR)/100
            value = int(self.data['items'][item]*var)
            reward_text.append(f"> {item} evaluated for {moneyfy(value)}")
            total_reward += value
        payout = int(total_reward/len(winning_players))
        more_than_one_winner_text = ""
        if len(winning_players) > 1:
            more_than_one_winner_text = f" and a payout of {moneyfy(payout)} to each player"
        net_text = "loss"
        if total_reward > winning_bid:
            net_text = "profit"
        reward_text.append(
            f"""This totals to a reward of {moneyfy(total_reward)}{more_than_one_winner_text}.
            That means that their bid had a net {net_text} of {moneyfy(abs(total_reward-winning_bid))}.""")
        await self.send("\n".join(reward_text))
        if winning_players:
            await self.score(winning_players,payout,True)
        for player in winning_players:
            self.money[player] -= int(winning_bid/len(winning_players))
    async def game_cleanup(self):
        await self.send(f"{self.mention(self.players)} had {game.wordify_iterable(moneyfy(self.money[player]) for player in self.players)} respectively leftover.")
        for player in self.players:
            if self.money[player] < 0:
                self.money[player] = int(self.money[player] * (1 + END_OF_GAME_INTEREST/100))
        self.points_format = lambda x: f"{moneyfy(x)} total"
        await self.score(self.players,self.money)


            

