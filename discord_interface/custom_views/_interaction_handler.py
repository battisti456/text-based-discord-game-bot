from discord_interface.custom_views._custom_view import Custom_View
import discord
from game.components.send import Interaction, Interaction_Content
from time import time


class Interaction_Handler:
    def __init__(self, cv: Custom_View):
        self.cv = cv

    async def handle_interaction(
        self, discord_interaction: discord.Interaction, content: Interaction_Content
    ):
        assert discord_interaction.data is not None
        response = await self.cv.gi.interact(
            Interaction(
                at_address=self.cv.address,
                with_sendable=self.cv.sendable,
                by_player=self.cv.gi.find_player(discord_interaction.user.id),
                at_time=time(),
                content=content,  # type:ignore
            )
        )
        self.cv.last_responses[Interaction_Handler] = response
        await self.cv.give_feedback(discord_interaction)
