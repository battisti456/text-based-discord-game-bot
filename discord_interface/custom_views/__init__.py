from discord_interface.custom_views.one_selectable_view import One_Selectable_View
from discord_interface.custom_views.one_text_field_view import One_Text_Field_View
from discord_interface.custom_views.options_and_text_field_view import (
    Options_And_Text_View,
)
from discord_interface.custom_views.button_select_view import Button_Select_View
from discord_interface.custom_views.infinite_select_view import Infinite_Select_View

import discord
from typing import TYPE_CHECKING
from discord_interface.common import MAX_OPTIONS_PER_SELECTABLE, Discord_Address

if TYPE_CHECKING:
    from discord_interface.discord_interface import Discord_Game_Interface
    from game.components.send.sendable.prototype_sendables import With_Options


def select_view(
    gi: "Discord_Game_Interface", address: Discord_Address, sendable: "With_Options"
) -> discord.ui.View:
    view: discord.ui.View
    if len(sendable.with_options) == 2 and sendable.max_selectable == 1:
        view = Button_Select_View(gi, address, sendable)
    elif len(sendable.with_options) > MAX_OPTIONS_PER_SELECTABLE:
        view = Infinite_Select_View(gi, address, sendable)
    else:
        view = One_Selectable_View(gi, address, sendable)
    return view
