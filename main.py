import json

import game_handler
from game.games import *


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
#testing(config)
gh = game_handler.Game_Handler(config)
gh.next_game= Elimination_Letter_Adder(gh)
gh.run()

"""
things to work on:
- add better support for changing or not changing answers in multiple choice questions
    -finished on base multiple choice!
    -add to secret base
    -add to text responses (will require on_message_delete and on_message_edit)
-add player message deletion? requires receiving player message ids somehow

TEXT RESPONSE NOT WORKING IN KITTENS!!!!!

-rewrite secret text response from scratch to avoid taske ending prematurely bug? I added something. We'll see.

add while waiting message prompts - sorta done. Won't notify, but now updates dynamcally
-test bidding base
"""