import json
import random
from typing import TypedDict, override

from config.config import config
from config.games_config import games_config
from game import correct_int, make_player_dict, merge_placements, score_to_placement
from game.components.game_interface import Game_Interface
from game.components.message import Message, make_bullet_points
from game.components.player_input import (
    Player_Input,
    Player_Single_Selection_Input,
    Player_Text_Input,
    run_inputs,
)
from game.components.response_validator import Validation
from game.game import Game
from utils.emoji_groups import NUMBERED_KEYCAP_EMOJI
from utils.grammar import ordinate, wordify_iterable
from utils.types import PlayerDict, PlayerId, PlayerPlacement

CONFIG = games_config['the_great_kitten_race']

DATA_PATH = config['data_path'] + '/' + CONFIG['data_path']
NUM_OBSTACLES = CONFIG['num_obstacles']

class Obstacle(TypedDict):
    stat_checks:list[str]
    loss_text:list[str]
    win_text:list[str]
class KittenConfig(TypedDict):
    win_penalty:tuple[int,int]
    loss_penalty:tuple[int,int]
    stat_limit:int
    point_limit:int
    stats:list[str]
    obstacles:dict[str,Obstacle]
class Kitten(TypedDict):
    name:str
    stats:dict[str,int]
    time:int

class The_Great_Kitten_Race(Game):
    def __init__(self,gi:Game_Interface):
        Game.__init__(self,gi)
        with open(DATA_PATH,'r') as file:
            self.kitten_config:KittenConfig = json.load(file)
            self.times:PlayerDict[int] = {}
    @override
    async def game_intro(self):
        await self.basic_send(
            "# Here y'all are, finally, at the great kitten race!\n" +
            "You have each spent the past year training your kitten to compete in our randomized obstacle course!\n" +
            f"You have made sure to allocate each of those {self.kitten_config['point_limit']} skill points gained into the stats you believe will be most valuable.\n" +
            f"Your kitten's skill determines how likely it is to succeed where 0 always fails and {self.kitten_config['stat_limit']} always succeeds.\n" +
            "If your kitten succeeds at an obstacle it won't loses as much time as kittens who fail.\n" +
            "If an obstacle requires multiple stat checks, then your kitten's success will be based on the average of those stats.\n" +
            "Now is the day where you kittens will finally race! The lowest time at the end wins!\n" +
            "All you can do now is watch and hope your training pulled off...."
        )
    @override
    async def _run(self):
        obstacles = random.choices(list(self.kitten_config["obstacles"]),k=NUM_OBSTACLES)
        obstacle_text_list:list[str] = []
        for obstacle_name in obstacles:
            obstacle:Obstacle = self.kitten_config['obstacles'][obstacle_name]
            formatted_stats:list[str] = list(f"**{stat}**" for stat in obstacle['stat_checks'])
            obstacle_text_list.append(
                f"An obstacle of **{obstacle_name}** which involves {wordify_iterable(formatted_stats)}."
            )
        await self.basic_send(
            "Before you began training you were told which obstacles would show up in today's competition:\n" +
            "\n".join(obstacle_text_list) + '\n' + 
            "So let's have you introduce your kittens!")
        
        stat_input_dict:dict[str,Player_Input] = {}

        bp = make_bullet_points(
            list(str(num) for num in range(self.kitten_config['stat_limit']+1)),
            list(NUMBERED_KEYCAP_EMOJI)
        )

        for stat in self.kitten_config['stats']:
            message = Message(
                content = f"How did you train your cat's **{stat}** stat?",
                bullet_points= bp
            )
            input = Player_Single_Selection_Input(
                name = f"choice of {stat} stat",
                players=self.unkicked_players,
                gi = self.gi,
                sender = self.sender,
                message=message
            )
            stat_input_dict[stat] = input
        def verify_points(player:PlayerId,value:int|None) -> Validation:
            if value is None:
                return (False,None)
            num_points = sum(correct_int(stat_input_dict[stat].responses[player]) for stat in self.kitten_config['stats'])
            if num_points > self.kitten_config['point_limit']:
                return (False,f"with a total of '{num_points}', exceeded the point limit of '{self.kitten_config['point_limit']}'")
            if num_points < self.kitten_config['point_limit']:
                return (False,f"with a total of '{num_points}', fell short of the point limit of '{self.kitten_config['point_limit']}'")
            return (True,None)
        for stat in self.kitten_config['stats']:
            stat_input_dict[stat]._response_validator = verify_points
        name_input = Player_Text_Input(
            name = "kitten name",
            players=self.unkicked_players,
            gi = self.gi,
            sender = self.sender,
            message = Message(
                content = "**And, what was your kitten's name again?**"
            )
        )
        #TODO #7 make inputs actually update each other or relax restrictions on stat inputs
        all_inputs = list(stat_input_dict[stat] for stat in self.kitten_config['stats']) + [name_input]
        
        await run_inputs(
            all_inputs,codependent=True
        )
        
        await self.kick_none_response(*all_inputs)
        
        def make_kitten() -> Kitten:
            return {'name':"",'stats':{},'time':-1}
        kittens:PlayerDict[Kitten] = make_player_dict(self.unkicked_players,make_kitten)
        for player in self.unkicked_players:
            name = name_input.responses[player]
            assert name is not None
            kittens[player]['name'] = name
            for stat in self.kitten_config['stats']:
                value = stat_input_dict[stat].responses[player]
                assert value is not None
                kittens[player]['stats'][stat] = value
            total:int = sum(kittens[player]["stats"][stat] for stat in self.kitten_config["stats"])
            ratio:float = self.kitten_config['point_limit']/total
            for stat in self.kitten_config['stats']:
                kittens[player]["stats"][stat] = int(kittens[player]["stats"][stat]*ratio)
        
        for obstacle_name in obstacles:
            obstacle:Obstacle = self.kitten_config['obstacles'][obstacle_name]
            kitten_text_list:list[str] = []
            stat_checks:list[str] = obstacle["stat_checks"]
            for player in self.unkicked_players:
                stat_threshold:float = sum(kittens[player]['stats'][stat] for stat in stat_checks)/len(stat_checks)/self.kitten_config['stat_limit']
                if random.random() < stat_threshold:#success
                    text = f"__*{kittens[player]['name']}*__ fortunately performed well. They {random.choice(obstacle['win_text'])} and only"
                    time_penalty = random.randint(self.kitten_config['win_penalty'][0],self.kitten_config['win_penalty'][1])
                else:#fail
                    text = f"__*{kittens[player]['name']}*__ unfortunately performed poorly. They {random.choice(obstacle['loss_text'])} and"
                    time_penalty = random.randint(self.kitten_config['loss_penalty'][0],self.kitten_config['loss_penalty'][1])
                kitten_text_list.append(f"{text} lost {time_penalty} seconds because of it.")
                kittens[player]['time'] += time_penalty
            await self.basic_send(
                f"Our kittens come across an obstacle of **{obstacle_name}**.\n" +
                '\n'.join(kitten_text_list)
            )
        
        order:list[PlayerId] = list(self.unkicked_players).copy()
        order.sort(key=lambda player:kittens[player]['time'])

        cross_finish_text_list:list[str] = list(
            f"Crossing {ordinate(i+1)} we have __*{kittens[order[i]]['name']}*__ " + 
            f"racing for {self.format_players_md([order[i]])} with a final time of " +
            f"{kittens[order[i]]['time']} seconds!" for i in range(len(order)))
        await self.basic_send(
            "Anxiously we await at the finish line. Who will be first? Then coming over the hill we see...\n"+
            '\n'.join(cross_finish_text_list)
            )
        
        self.times = {player:kittens[player]['time'] for player in self.unkicked_players}
    @override
    def generate_placements(self) -> PlayerPlacement:
        return merge_placements(
            score_to_placement(self.times,self.all_players),
            self.generate_kicked_placements()
        )



