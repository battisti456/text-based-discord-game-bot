from config.config_tools import DiscordConfigDict, merge_local

discord_config:DiscordConfigDict = {
    "token" : "_______" #add your own bot's token in your local config"
}

merge_local('discord_config',discord_config) #type: ignore
