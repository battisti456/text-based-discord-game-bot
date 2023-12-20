import game
from game import userid
import random
from game.emoji_groups import NUMBERED_KEYCAP_EMOJI

import json
import asyncio

from typing import TypedDict, Callable, Awaitable

DATA_PATH = "kitten_race_obstacles.json"
NUM_OBSTACLES = 5

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
    obstacles:list[Obstacle]
class Kitten(TypedDict):
    name:str
    stats:dict[str,int]
    time:int

class The_Great_Kitten_Race(game.Game):
    def __init__(self,gh:game.GH):
        game.Game.__init__(self,gh)
        with open(self.config['data_path'] + "\\" + DATA_PATH,'r') as file:
            self.kitten_config:KittenConfig = json.load(file)
    async def run(self) -> list[userid|list[userid]]:
        await self.send(
            "# Here y'all are, finally, at the great kitten race!\n" +
            "You have each spent the past year training your kitten to compete in our randomized obstacle course!\n" +
            f"You have made sure to allocate each of those {self.kitten_config['point_limit']} skill points gained into the stats you believe will be most valuable.\n" +
            f"Your kitten's skill determines how likely it is to succeed where 0 always fails and {self.kitten_config['stat_limit']} always succeeds.\n" +
            "If your kitten succeeds at an obstacle it won't loses as much time as kittens who fail\n." +
            "If an obstacle requires multiple stat checks, then your kitten's success will be based on the average of those stats.\n" +
            "Now is the day where you kittens will finally race! The lowest time at the end wins!\n" +
            "All you can do now is watch and hope your training pulled off...."
        )
        obstacles = random.choices(list(self.kitten_config["obstacles"]),k=NUM_OBSTACLES)
        obstacle_text_list:list[str] = []
        for obstacle_name in obstacles:
            obstacle:Obstacle = self.kitten_config['obstacles'][obstacle_name]
            formatted_stats:list[str] = list(f"**{stat}**" for stat in obstacle['stat_checks'])
            obstacle_text_list.append(
                f"An obstacle of **{obstacle_name}** which involves {game.wordify_iterable(formatted_stats)}."
            )
        await self.send(
            f"Before you began training you were told which obstacles would show up in today's competition.\n" +
            "\n".join(obstacle_text_list) + '\n' + 
            "So let's have you introduce your kittens!")
        question_stat_dict:dict[str,str] = {}
        question_is_done_dict:dict[str,bool] = {}
        question_storage_dict:dict[str,str|int] = {}
        tasks:list[asyncio.Task] = []
        options = list(f"{point}" for point in range(self.kitten_config['stat_limit']+1))
        
        questions_finished:dict[str|int,bool] = {
            0: False
        }
        def make_sync_lock(question:str) -> Callable[[bool],Awaitable[bool]] :
            questions_finished[question] = False
            async def sync_lock(is_done:bool) -> bool:
                if questions_finished[0]:
                    return True
                else:
                    questions_finished[question] = is_done
                    questions_finished[0] = all(questions_finished[q] for q in questions_finished if q != 0)
                    if questions_finished[0]:
                        return True
                return False
            return sync_lock()

        for stat in self.kitten_config['stats']:
            question = f"How did you train your cat's **{stat}** stat?"
            question_stat_dict[question] = stat
            question_is_done_dict[question] = False
            tasks.append(asyncio.Task(self.multiple_choice(question,options,self.players,NUMBERED_KEYCAP_EMOJI,sync_lock=make_sync_lock(question))))
        name_question:str = "Also, what was you kitten's name again?"
        question_is_done_dict[name_question] = False
        tasks.append(asyncio.Task(self.text_response(name_question,self.players,sync_lock=make_sync_lock(name_question))))
        await asyncio.wait(tasks)

        kittens:dict[userid,Kitten] = {}
        for player in self.players:
            kittens[player] = {}
            kittens[player]['name'] = question_storage_dict[name_question][player]
            kittens[player]['stats'] = {}
            kittens[player]["time"] = 0
            for stat_question in question_stat_dict:
                kittens[player]["stats"][question_stat_dict[stat_question]] = question_storage_dict[stat_question][player]
            total:int = sum(kittens[player]["stats"][stat] for stat in self.kitten_config["stats"])
            ratio:float = self.kitten_config['point_limit']/total
            for stat in self.kitten_config['stats']:
                kittens[player]["stats"][stat] = int(kittens[player]["stats"][stat]*ratio)
        
        for obstacle_name in obstacles:
            obstacle:Obstacle = self.kitten_config['obstacles'][obstacle_name]
            kitten_text_list:list[str] = []
            stat_checks:list[str] = obstacle["stat_checks"]
            for player in self.players:
                stat_treshold:float = sum(kittens[player]['stats'][stat] for stat in stat_checks)/len(stat_checks)/self.kitten_config['stat_limit']
                if random.random() < stat_treshold:#success
                    text = f"__*{kittens[player]['name']}*__ fortunately peformed well. They {random.choice(obstacle['win_text'])} and only"
                    time_penalty = random.randint(self.kitten_config['win_penalty'][0],self.kitten_config['win_penalty'][1])
                else:#fail
                    text = f"__*{kittens[player]['name']}*__ unfortunately performed poorly. They {random.choice(obstacle['loss_text'])} and"
                    time_penalty = random.randint(self.kitten_config['loss_penalty'][0],self.kitten_config['loss_penalty'][1])
                kitten_text_list.append(f"{text} lost {time_penalty} seconds because of it.")
                kittens[player]['time'] += time_penalty
            await self.send(
                f"Our kittens come across an obstacle of **{obstacle_name}**.\n" +
                '\n'.join(kitten_text_list)
            )
        
        placements:list[userid] = list(self.players).copy()
        placements.sort(key=lambda player:kittens[player]['time'])

        cross_finish_text_list:list[str] = list(
            f"Crossing {game.ordinate(i+1)} we have __*{kittens[placements[i]]['name']}*__ " + 
            f"racing for {self.mention(placements[i])} with a final time of " +
            f"{kittens[placements[i]]['time']} seconds!" for i in range(len(placements)))
        await self.send(
            f"Anxiously we await at the finish line. Who will be first? Then coming over the hill we see...\n"+
            '\n'.join(cross_finish_text_list)
            )
        return placements



