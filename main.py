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
testing(config)
gh = game_handler.Game_Handler(config)
gh.next_game= Elimination_Blackjack(gh)
gh.run()

"""
things to work on:
- add better support for changing or not changing answers in multiple choice questions
    -finished on base multiple choice!
    -add to secret base
    -add to text responses (will require on_message_delete and on_message_edit)
-test bidding base
-add player message deletion?

-rewrite secret text response from scratch to avoid taske ending prematurely bug? I added something. We'll see.

add while waiting message prompts
"""