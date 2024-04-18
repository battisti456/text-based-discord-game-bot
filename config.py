from typing import TypedDict

from game import PlayerId

class ConfigDict(TypedDict):
    command_prefix:str
    command_users:list[PlayerId]

config:ConfigDict = {
    'command_prefix' : ">> ",
    "command_users" : [] # users permitted to use the game_operator commands over message when using the command_prefix symbol
}

try:
    from config_local import config as config_local
    for key in config_local:
        if key in config:
            config[key] = config_local[key]
except ImportError:
    ...# local config not set up
