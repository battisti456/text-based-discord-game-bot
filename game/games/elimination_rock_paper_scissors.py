#NEEDS TO BE TESTED
from game.utils.types import PlayerId, PlayerDict
from game import make_player_dict
from game.game_bases import Elimination_Base
from game.components.game_interface import Game_Interface
from game.components.response_validator import single_choice_validator_maker
from game.utils.emoji_groups import ROCK_PAPER_SCISSORS_EMOJI
import random

class Elimination_Rock_Paper_Scissors(Elimination_Base):
    def __init__(self,gi:Game_Interface):
        Elimination_Base.__init__(self,gi)
        self.guns:PlayerDict[int] = make_player_dict(self.unkicked_players,0)
        self.announced_guns:bool = False
    async def game_intro(self):
        await self.basic_send(
            "# Welcome to a game of elimination rock paper scizzors!\n" +
            "In this game you can choose to throw rock paper or scizzors.\n" +
            "Then I will tell you what I picked.\n" +
            "If I beat you, you are eliminated!")
    async def core_game(self):
        options = ['rock','paper','scissors']
        players_with_guns = list(player for player in self.unkicked_players if self.guns[player] > 0)
        gun_text = ""
        if players_with_guns:
            options.append('gun')
            gun_owners:list[list[PlayerId]] = []
            for player in players_with_guns:
                while len(gun_owners) < self.guns[player]:
                    gun_owners.append([])
                gun_owners[self.guns[player]-1].append(player)
            gun_text_list:list[str] = []
            for num_guns in range(len(gun_owners)):
                s = "s"
                if num_guns == 0:
                    s = ""
                if len(gun_owners[num_guns]) == 1:
                    gun_text_list.append(f"{self.format_players(gun_owners[num_guns])} has {num_guns + 1} gun{s}.")
                elif gun_owners[num_guns]:
                    gun_text_list.append(f"{self.format_players(gun_owners[num_guns])} have {num_guns + 1} gun{s} each.")
            gun_text= '\n'.join(gun_text_list)
            #gun_text = f"\n{gun_text}\nRemember that if you choose gun without having one, you lose!\n"
        responses:PlayerDict[int] = await self.basic_multiple_choice(
            content = f"What move will you choose?{gun_text}",
            options = options,
            who_chooses=self.unkicked_players,
            emojis=list(ROCK_PAPER_SCISSORS_EMOJI),
            response_validator=single_choice_validator_maker(
                {player:set(range(3)) for player in self.unkicked_players if not player in players_with_guns},
                list(ROCK_PAPER_SCISSORS_EMOJI)))
        my_pick = random.randint(0,2)
        players_eliminated:list[PlayerId] = []
        players_who_won_guns:list[PlayerId] = []
        for player in self.unkicked_players:
            if responses[player] < 3:
                if responses[player] == my_pick:#tie
                    pass
                elif responses[player] == (my_pick+1)%3:#they win
                    players_who_won_guns.append(player)
                    self.guns[player] += 1
                else:#they lose
                    players_eliminated.append(player)
            else:
                if self.guns[player] > 0:#they used a gun
                    self.guns[player] -= 1
                else:#they tried to use a gun, but didn't have one
                    players_eliminated.append(player)
        await self.basic_send(f"I threw a {ROCK_PAPER_SCISSORS_EMOJI[my_pick]}.")
        if players_who_won_guns and len(self.unkicked_players) - len(players_eliminated) > 1:
            await self.basic_send(
                f"{self.format_players_md(players_who_won_guns)} picked {ROCK_PAPER_SCISSORS_EMOJI[(my_pick+1)%3]} " +
                "thereby defeating me and winning a gun!")
            if not self.announced_guns:
                self.announced_guns = True
                await self.basic_send(
                    "Woah, plot twist!. If you beat me you get a gun you can pick instead in the next round. It will gurantee you a pass for the round!")
        await self.eliminate(players_eliminated)
        
