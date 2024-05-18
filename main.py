import sys

from config.config import config
from config.discord_config import discord_config
from discord_interface import Discord_Game_Interface
from game.components.game_operator import Game_Operator

if __name__ == "__main__":
    gi = Discord_Game_Interface(config['main_channel_id'],config['players'])
    go = Game_Operator(gi)
    @gi.client.event
    async def on_ready():
        text = ""
        if len(sys.argv) > 1:
            text = f"{sys.argv[1]}\n"
        await go.basic_send(
            f"{text}The game bot is ready. If you are a command user, please input '{config['command_prefix']} run_game' to start a random game, or '{config['command_prefix']} help' to see more options."
        )
    gi.client.run(discord_config['token'])
