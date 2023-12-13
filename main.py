import json

import game_handler
from game.games import *

working = [Guess_The_Word,Elimination_Letter_Adder,Elimination_Trivia,Longest_Word,Fibbage_At_Home]#i hope
played = [Elimination_Letter_Adder,Elimination_Trivia]

CONFIG_PATH = "gamebotconfig.json"

def grab_json(path):
    assert isinstance(path,str)
    with open(path,'r') as file:
        to_return = json.load(file)
    return to_return

def testing(config):
    config['channel_id'] = config['test_channel_id']
    config['players'] = config['test_players']

config = grab_json(CONFIG_PATH)
testing(config)
gh = game_handler.Game_Handler(config)
gh.next_game= Container_Bidding(gh)
gh.run()

"""
things to work on:
- add better support for changing or not changing answers in multiple choice questions
--card base svg is unfixable methinks. so, convert to png
-include max debt into container bidding
-partial share system container biddin?
-implement bidding base into container bidding
-test bidding base
-add player message deletion?

-rewrite secret text response from scratch to avoid taske ending prematurely bug?
"""