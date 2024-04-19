from typing import TypedDict

class GamesConfigDict(TypedDict):
    ...

games_config:GamesConfigDict = {
    
}

try:
    from games_config_local import games_config as games_config_local
    for key in games_config_local:
        if key in games_config:
            games_config[key] = games_config_local[key]
except ImportError:
    ...# local config not set up
