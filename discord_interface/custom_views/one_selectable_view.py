from typing import TYPE_CHECKING, override

import discord

from discord_interface.common import Discord_Address
from discord_interface.custom_views._custom_view import Custom_View
from discord_interface.custom_views._interaction_handler import Interaction_Handler
from game.components.send.interaction import Select_Options
from game.components.send.option import Option
from game.components.send.sendable.prototype_sendables import With_Options
from utils.common import get_first

if TYPE_CHECKING:
    from discord_interface.discord_interface import Discord_Game_Interface


class Select(discord.ui.Select, Interaction_Handler):
    def __init__(self, cv: Custom_View[With_Options]):
        self.cv = cv
        Interaction_Handler.__init__(self, cv)
        self.game_discord_option_map: "dict[Option,discord.SelectOption]" = {
            option: discord.SelectOption(
                label=option.text, emoji=option.emoji, description=option.long_text
            )
            for option in self.cv.sendable.with_options
        }
        kwargs = {}
        if self.cv.sendable.min_selectable is not None:
            kwargs["min_values"] = self.cv.sendable.min_selectable
        if self.cv.sendable.max_selectable is not None:
            kwargs["max_values"] = self.cv.sendable.max_selectable
        discord.ui.Select.__init__(
            self,  # could add placeholder
            options=list(
                self.game_discord_option_map[option]
                for option in self.cv.sendable.with_options
            ),
            **kwargs,
        )

    @override
    async def callback(self, discord_interaction: "discord.Interaction"):
        options: tuple[Option, ...] = tuple(
            get_first(
                option
                for option in self.cv.sendable.with_options
                if option.text == value
            )
            for value in discord_interaction.data["values"]  # type:ignore
        )
        indices: tuple[int, ...] = tuple(
            self.cv.sendable.with_options.index(option) for option in options
        )
        await self.handle_interaction(
            discord_interaction, Select_Options(options, indices)
        )


class One_Selectable_View(Custom_View):
    def __init__(
        self,
        gi: "Discord_Game_Interface",
        address: "Discord_Address",
        sendable: "With_Options",
    ):
        super().__init__(gi, address, sendable)
        self.add_item(Select(self))
