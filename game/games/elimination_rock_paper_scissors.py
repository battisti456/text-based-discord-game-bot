import game
from game import userid
from game.game_bases import Elimination_Base
from game.emoji_groups import ROCK_PAPER_SCISSORS_EMOJI
import random

class Elimination_Rock_Paper_Scissors(Elimination_Base):
    def __init__(self,gh:game.GH):
        Elimination_Base.__init__(self,gh)
        self.guns:list[userid,int] = self.make_player_dict(0)
        self.announced_guns:bool = False
    async def game_intro(self):
        await self.send(f"""# Welcome to a game of elimination rock paper scizzors!
                        In this game you can choose to throw rock paper or scizzors.
                        Then I will tell you what I picked.
                        If I beat you, you are eliminated!""")
    async def core_game(self, remaining_players: list[int]) -> list[int]:
        options = ['rock','paper','scissors']
        players_with_guns = list(player for player in remaining_players if self.guns[player] > 0)
        gun_text = ""
        if players_with_guns:
            options.append('gun')
            gun_owners:list[list[userid]] = []
            for player in self.guns:
                while len(gun_owners) < self.guns[player]:
                    gun_owners.append([])
                gun_owners[self.guns[player]-1].append(player)
            gun_text_list:list[str] = []
            for num_guns in range(len(gun_owners)):
                s = "s"
                if num_guns == 0:
                    s = ""
                if len(gun_owners[num_guns]) == 1:
                    gun_text_list.append(f"{self.mention(gun_owners[num_guns])} has {num_guns + 1} gun{s}.")
                elif gun_owners[num_guns]:
                    gun_text_list.append(f"{self.mention(gun_owners[num_guns])} have {num_guns + 1} gun{s} each.")
            gun_text= '\n'.join(gun_text_list)
            gun_text = f"\n{gun_text}\nRemember that if you choose gun without having one, you lose!\n"
        responses:dict[userid,int] = await self.multiple_choice(f"What move will you choose?{gun_text}",options,remaining_players,ROCK_PAPER_SCISSORS_EMOJI)
        my_pick = random.randint(0,2)
        players_eliminated:list[userid] = []
        players_who_won_guns:list[userid] = []
        for player in remaining_players:
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
        await self.send(f"I threw a {ROCK_PAPER_SCISSORS_EMOJI[my_pick]}.")
        if players_who_won_guns and len(remaining_players) - len(players_eliminated) > 1:
            await self.send(f"{self.mention(players_who_won_guns)} picked {ROCK_PAPER_SCISSORS_EMOJI[(my_pick+1)%3]} thereby defeating me and winning a gun!")
            if not self.announced_guns:
                self.announced_guns = True
                await self.send("Woah, plot twist!. If you beat me you get a gun you can pick instead in the next round. It will gurantee you a pass for the round!")
        return players_eliminated
        
