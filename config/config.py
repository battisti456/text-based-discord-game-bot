from config.config_tools import ConfigDict, merge_local

config:ConfigDict = {
    'command_prefix' : ">> ",
    "command_users" : [], # users permitted to use the game_operator commands over message when using the command_prefix symbol
    "main_channel_id" : 0,#type: ignore
    "players" : [],
    "temp_path":"temp",
    "data_path":"data",
    "default_timeout" : 86400,#24 h
    "default_warnings": [43200,72000,82800],#12 h, 20 h, 23 h
    "profanity_threshold" : 0.5,#to disable set >1
    "python_cmd" : 'python',
    "main" : "main.py"
}

merge_local('config',config) #type: ignore
