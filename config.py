from typing import TypedDict

from game import PlayerId, ChannelId

class ConfigDict(TypedDict):
    command_prefix:str
    command_users:list[PlayerId]
    main_channel_id:ChannelId
    players:list[PlayerId]
    temp_path:str
    data_path:str
    default_timeout:int
    default_warnings:list[int]

config:ConfigDict = {
    'command_prefix' : ">> ",
    "command_users" : [], # users permitted to use the game_operator commands over message when using the command_prefix symbol
    "main_channel_id" : 0,
    "players" : [],
    "temp_path":"temp",
    "data_path":"data",
    "default_timeout" : 86400,#24 h
    "default_warnings": [43200,72000,82800]#12 h, 20 h, 23 h
}

try:
    from config_local import config as config_local
    for key in config_local:
        if key in config:
            config[key] = config_local[key]
except ImportError:
    ...# local config not set up
