import json
import asyncio

from discord_interface import Discord_Game_Interface
from game.games import *

from typing import TypedDict

class Config(TypedDict):
    channel_id:int
    players:dict[str,int]
    test_channel_id:int
    test_players:dict[str,int]
    token:str

CONFIG_PATH = "gamebotconfig.json"

def grab_json(path):
    assert isinstance(path,str)
    with open(path,'r') as file:
        to_return = json.load(file)
    return to_return

def testing(config:Config):
    config['channel_id'] = config['test_channel_id']
    config['players'] = config['test_players']

config:Config = grab_json(CONFIG_PATH)
testing(config)

gi = Discord_Game_Interface(config['channel_id'],list(config['players'][player] for player in config['players']))
gm = Longest_Word(gi)
asyncio.create_task(gm.run())
gi.client.run(config['token'])