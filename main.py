import sys

from config import Config as config
from config.discord_config import discord_config
from discord_interface import Discord_Game_Interface
from game.components.game_operator import Game_Operator


if __name__ == "__main__":
    gi = Discord_Game_Interface(discord_config['main_channel_id'],discord_config['player_ids'])
    @gi.on_start
    async def on_ready():
        await gi.reset()
        go = Game_Operator(gi)
        text = ""
        if len(sys.argv) > 1:
            text = f"{sys.argv[1]}\n"
        await go.send(
            text=f"{text}The game bot is ready. If you are a command user, please input '{config['command_prefix']} run_game' to start a random game, or '{config['command_prefix']} help' to see more options."
        )
    gi.client.run(discord_config['token'])
