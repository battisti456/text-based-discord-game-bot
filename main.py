from discord_interface import Discord_Game_Interface
from game.games import *

from config import config
from discord_config import discord_config


if __name__ == "__main__":
    gi = Discord_Game_Interface(config['main_channel_id'],config['players'])
    @gi.client.event
    async def on_ready():
        await gi.reset()
        while True:
            gm = random_game()(gi)
            await gm.run()
            await gm.basic_send_placement(gm.generate_placements())
    gi.client.run(discord_config['token'])
