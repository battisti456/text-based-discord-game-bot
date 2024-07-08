import json
import random
from typing import TypedDict, override

from config.config import config
from config.games_config import games_config
from game import make_player_dict
from game.components.game_interface import Game_Interface
from game.components.participant import Player
from game.game_bases import Rounds_With_Points_Base
from utils.grammar import wordify_iterable, moneyfy
from utils.types import PlayerDict

CONFIG = games_config['container_bidding']

NUM_CONTAINERS = CONFIG['num_containers']
DATA_PATH = config['data_path'] + '\\' + CONFIG['data_path']
STARTING_MONEY = CONFIG['starting_money']
PERCENTILE_VAR = CONFIG['percentile_var']
END_OF_GAME_INTEREST = CONFIG['end_of_game_interest']

class DescDict(TypedDict):
    starting_bid_range:tuple[int,int]
    num_items_range:tuple[int,int]
    possible_item_tiers:dict[str,int]
class DataDict(TypedDict):
    container_descriptions:dict[str,DescDict]
    container_types:dict[str,dict[str,int]]
    items:dict[str,int]

def validate_data(data:DataDict):
    for desc_text in data["container_descriptions"]:
        for tier_text in data["container_descriptions"][desc_text]["possible_item_tiers"]:
            if tier_text not in data["container_types"]:
                raise Exception(f"In container data tier '{tier_text}' from desc '{desc_text}' is undefined.")
    for tier in data["container_types"]:
        for item in data["container_types"][tier]:
            if item not in data["items"]:
                raise Exception(f"In container data item '{item}' from tier '{tier}'is undefined.")
#TODO: #10 The main game loop doesn't quite make sense, and it often makes more sense not to bid for items than to bid for items.
class Container_Bidding(Rounds_With_Points_Base):
    def __init__(self,gi:Game_Interface):
        Rounds_With_Points_Base.__init__(self,gi)
        self.num_rounds = NUM_CONTAINERS
        self.round_name = "bidding on container"
        self.point_frmt = lambda num: f"{moneyfy(num)} of valuables"
        with open(f"{DATA_PATH}",'r') as file:
            self.data:DataDict = json.load(file)
        validate_data(self.data)
        self.money:PlayerDict[int] = make_player_dict(self.unkicked_players,int(STARTING_MONEY/len(self.unkicked_players)))
    @override
    async def game_intro(self):
        await self.say(
            "# Welcome to a game of container bidding!\n" + 
            f"In this game we will have {NUM_CONTAINERS} containers that we look at.\n" +
            "For each container my expert evaluator will provide their description.\n" +
            "Then you must each secretly choose how much you would be willing to contribute for it!\n" +
            "All of you are bidding together, but each secretly deciding how much to contribute.\n" +
            "The proportion of the total bid that your contribution takes up determines your share of the valuables inside the container.\n" +
            f"If your cumulative bidding exceeds your starting cash of {moneyfy(int(STARTING_MONEY/len(self.unkicked_players)))}, " +
            f"then you will lose an extra {END_OF_GAME_INTEREST}% at the end of the game for interest for all money spent in excess of that.\n"+
            "Any money you don't end up spending will be added to your total at the end of the game.\n"
            "**WARNING: Your answers are only evaluated based of the digits they contain. All other characters are ignored. So '$100.00' is '$10000'.**")
    def evaluate_container(self,desc:DescDict) -> tuple[int,list[str]]:
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
        return total_reward, reward_text
    @override
    async def core_round(self):
        desc_name:str = random.choice(list(self.data["container_descriptions"]))
        desc:DescDict = self.data['container_descriptions'][desc_name]
        total_bid_threshold:int = random.randint(desc["starting_bid_range"][0],desc["starting_bid_range"][1])
        question_text:str = (
            f"Our expert evaluator described this container as '{desc_name}'.\n"+
            f"The total bid threshold is {moneyfy(total_bid_threshold)}.\n" +
            f"I would suggest contributing 1/{len(self.unkicked_players)} of this. " +
            f"So, {int(total_bid_threshold/len(self.unkicked_players))}.\n" +
            "How much are you willing to contribute?")
        await self.say(f"{question_text}\nPlease respond in your private channel.")
        #TODO: #9 should add validification to this response
        responses = await self.basic_text_response(
            content="How much would you like to contribute for this bid?",
            who_chooses=self.unkicked_players
            )
        player_bids:dict[Player,int] = make_player_dict(self.unkicked_players,0)
        for player in self.unkicked_players:
            response:str = responses[player]
            response_only_num:str = "".join(list(num for num in response if num.isdigit()))
            if response_only_num != "":
                player_bids[player] = int(response_only_num)

        total_bid:int = sum(player_bids[player] for player in player_bids)
        if total_bid >= total_bid_threshold:
            total_reward, reward_text = self.evaluate_container(desc)
            player_split_text = f"It will be split {len(player_bids)} way(s) between {self.format_players_md(list(player_bids))} according to the amounts they contributed to the bid."
            if len(player_bids) == 1:
                player_split_text = f"{self.format_players_md(list(player_bids))} has won the whole amount."
            await self.say(
                f"Your total bid of {moneyfy(total_bid)} exceeded our bid threshold of {moneyfy(total_bid_threshold)}.\n" +
                "\n".join(reward_text) + '\n' +
                f"The total contents of this container are worth {moneyfy(total_reward)}.\n" +
                player_split_text)
            for player in player_bids:
                self.money[player] -= player_bids[player]
                player_portion = player_bids[player]/total_bid
                player_return = int(total_reward*player_portion)
                await self.score(player,player_return,True)
        else:
            await self.say(
                f"Your total bid of {moneyfy(total_bid)} didn't exceed our bid threshold of {moneyfy(total_bid_threshold)}.\n" +
                "Y'all have decided to pass on this container. Ah well.")
    async def game_cleanup(self):
        await self.say(
            "That was our last container, so, at the end of the game: "+
            f"{self.format_players_md(self.unkicked_players)} had {wordify_iterable(moneyfy(self.money[player]) for player in self.unkicked_players)} leftover respectively." +
            f"This remaining money will be added to your final money score, but any negatives will be charged an extra {END_OF_GAME_INTEREST}% in interest.")
        for player in self.unkicked_players:
            if self.money[player] < 0:
                self.money[player] = int(self.money[player] * (1 + END_OF_GAME_INTEREST/100))
        self.points_format = lambda x: f"{moneyfy(x)} total"
        await self.score(self.unkicked_players,self.money)


            

