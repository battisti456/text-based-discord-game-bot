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
gh.next_game= Emoji_Communication(gh)
gh.run()

"""
things to work on:
-add who hasn't responded message to secret base main thread

add while waiting message prompts - sorta done. Won't notify, but now updates dynamcally

-big picture changes:
change format a bit
    create game_interface object
    change game_handler to be a discord version of game_interface
    change userid,messageid, and channelid to be objects User, Message, Channel (with all nessasry functionality)
    and hopefully fix import order a bit better because of it
    add Question or User_Prompty type too, hopeffuly fix all the spaghetti code of the current various question and send functions
    add a Sync object to get rid of the horrers that is the current Sync_Lock implementation


-minor
fix gitignore so git only includes files I made
test bidding base- will anything even use it?
retest letter adder
test aig


-priorities!
considering there isn't much time left, priority should probably go to fixing it up so it can actually be shown on github, although overhauling everything would be nice too....
"""