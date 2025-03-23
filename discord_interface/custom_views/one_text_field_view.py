from typing import TYPE_CHECKING, override

import discord

from discord_interface.common import Discord_Address
from discord_interface.custom_views._common import hint_text
from discord_interface.custom_views._custom_view import Custom_View
from discord_interface.custom_views._interaction_handler import Interaction_Handler
from game.components.send.interaction import Send_Text
from game.components.send.sendable.prototype_sendables import With_Text_Field

if TYPE_CHECKING:
    from discord_interface.discord_interface import Discord_Game_Interface


class Text_Input(discord.ui.TextInput):
    def __init__(self, cv: Custom_View[With_Text_Field]):
        self.cv = cv
        super().__init__(label=hint_text(self.cv.sendable))


class Text_Input_Modal(discord.ui.Modal, Interaction_Handler):
    def __init__(self, cv: Custom_View):
        super().__init__(title="Input text here:")
        Interaction_Handler.__init__(self, cv)
        self.add_item(Text_Input(cv))

    @override
    async def on_submit(self, discord_interaction: discord.Interaction):
        await self.handle_interaction(
            discord_interaction,
            Send_Text(
                discord_interaction.data["components"][0]["components"][0]["value"]  # type:ignore
            ),
        )


class Text_Input_Button(discord.ui.Button):
    def __init__(self, cv: Custom_View[With_Text_Field]):
        self.cv = cv
        super().__init__(label=hint_text(self.cv.sendable))

    @override
    async def callback(self, discord_interaction: discord.Interaction):
        await discord_interaction.response.send_modal(Text_Input_Modal(self.cv))
        return await super().callback(discord_interaction)


class One_Text_Field_View(Custom_View):
    def __init__(
        self,
        gi: "Discord_Game_Interface",
        address: "Discord_Address",
        sendable: "With_Text_Field",
    ):
        super().__init__(gi, address, sendable)
        self.add_item(Text_Input_Button(self))
