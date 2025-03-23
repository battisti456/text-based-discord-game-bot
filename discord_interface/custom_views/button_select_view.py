import discord
from typing import TYPE_CHECKING, override
from discord_interface.custom_views._custom_view import Custom_View
from game.components.send.interaction import Select_Options
from discord_interface.custom_views._interaction_handler import Interaction_Handler

if TYPE_CHECKING:
    from discord_interface.discord_interface import Discord_Game_Interface
    from discord_interface.common import Discord_Address
    from game.components.send.sendable.prototype_sendables import With_Options


class Button_Select(discord.ui.Button, Interaction_Handler):
    def __init__(self, cv: "Button_Select_View", index: int, row: int | None = None):
        self.cv = cv
        self.index = index
        self.option = self.cv.sendable.with_options[self.index]
        super().__init__(label=self.option.text, emoji=self.option.emoji, row=row)

    @override
    async def callback(self, discord_interaction: discord.Interaction):
        await self.handle_interaction(
            discord_interaction,
            Select_Options(options=(self.option,), indices=(self.index,)),
        )
        return await super().callback(discord_interaction)


class Button_Select_View(Custom_View["With_Options"]):
    def __init__(
        self,
        gi: "Discord_Game_Interface",
        address: "Discord_Address",
        sendable: "With_Options",
    ):
        super().__init__(gi, address, sendable)
        self.num_options: int = len(sendable.with_options)
        self.dim = int(self.num_options**0.5)
        for row in range(self.dim):
            for index in range(self.dim):
                index = row * self.dim + index
                self.add_item(Button_Select(self, index, row))
        for index in range((row + 1) * self.dim, self.num_options):
            self.add_item(Button_Select(self, index, row + 1))
