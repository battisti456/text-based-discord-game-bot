from typing import TYPE_CHECKING
from discord_interface.custom_views._custom_view import Custom_View
from discord_interface.custom_views.one_selectable_view import Select
from discord_interface.custom_views.one_text_field_view import Text_Input_Button

if TYPE_CHECKING:
    from discord_interface.discord_interface import Discord_Game_Interface
    from discord_interface.common import Discord_Address
    from game.components.send.sendable.prototype_sendables import With_Text_Field


class Options_And_Text_View(Custom_View):
    def __init__(
        self,
        gi: "Discord_Game_Interface",
        address: "Discord_Address",
        sendable: "With_Text_Field",
    ):
        super().__init__(gi, address, sendable)
        self.add_item(Text_Input_Button(self))
        self.add_item(Select(self))
