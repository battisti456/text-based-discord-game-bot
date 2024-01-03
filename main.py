import json
import asyncio
import game
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
gm = The_Great_Kitten_Race(gi)
@gi.client.event
async def on_ready():
    await gi.client.wait_until_ready()
    channel = gi.client.get_channel(config['channel_id'])
    for thread in channel.threads:
        await thread.delete()

    asyncio.create_task(gm.run())
gi.client.run(config['token'])