from typing import TypedDict

class DiscordConfigDict(TypedDict):
    token:str

discord_config:DiscordConfigDict = {
    "token" : "_______" #add your own bot's token in your local config"
}

try:
    from discord_config_local import discord_config as discord_config_local
    for key in discord_config_local:
        if key in discord_config:
            discord_config[key] = discord_config_local[key]
except ImportError:
    ...# local config not set up
