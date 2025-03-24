from math import ceil
from time import time
from typing import TYPE_CHECKING, override

import discord

from discord_interface.common import MAX_OPTIONS_PER_SELECTABLE, Discord_Address
from discord_interface.custom_views._custom_view import Custom_View
from game.components.send.interaction import Interaction, Select_Options
from game.components.send.option import Option
from game.components.send.sendable.prototype_sendables import With_Options
from utils.common import get_first
from utils.emoji_groups import LEFT_RIGHT_EMOJI, LIST
from utils.grammar import s, wordify_iterable
from utils.logging import get_logger

logger = get_logger(__name__)


if TYPE_CHECKING:
    from discord_interface.discord_interface import Discord_Game_Interface


class _Infinite_Select_View(discord.ui.View):
    def __init__(self, ivm: "Infinite_View_Manager"):
        super().__init__()
        self.ivm = ivm
        self.add_item(self.ivm.selections[self.ivm.page])
        if self.ivm.page != 0:
            self.add_item(self.ivm.left_button)
        if self.ivm.page != self.ivm.total_pages - 1:
            self.add_item(self.ivm.right_button)
        if not self.ivm.single_select:
            self.add_item(self.ivm.confirm_button)


class _Infinite_Selection(discord.ui.Select):
    def __init__(self, ivm: "Infinite_View_Manager", page: int):
        self.ivm = ivm
        self.offset = page * MAX_OPTIONS_PER_SELECTABLE
        self.number_selected = 0
        self.currently_selected: tuple[Option, ...] = ()
        super().__init__(
            row=0,
            options=list(
                discord.SelectOption(
                    label=option.text, emoji=option.emoji, description=option.long_text
                )
                for option in self.ivm.cv.sendable.with_options[self.offset:self.offset+MAX_OPTIONS_PER_SELECTABLE]
            ),
        )
    def update(self):
        self.disabled = False
        selected_elsewhere = self.ivm.selected - self.number_selected
        min = self.ivm.min_select - selected_elsewhere
        if min < 0:
            min = 0
        max = self.ivm.max_select - selected_elsewhere
        if max > len(self.options):
            max = len(self.options)
        self.min_values = min
        if max < 1:
            self.disabled = True
            self.max_values = 1
        else:
            self.max_values = max

    @override
    async def callback(self, discord_interaction: discord.Interaction):
        options_selected: tuple[Option, ...] = tuple(
            get_first(
                option
                for option in self.ivm.cv.sendable.with_options
                if option.text == value
            )
            for value in discord_interaction.data["values"]  # type:ignore
        )
        self.currently_selected = options_selected
        self.ivm.selected += len(options_selected) - self.number_selected
        self.number_selected = len(options_selected)
        if self.number_selected == 1 and self.ivm.single_select:
            await self.ivm.generate_interaction(discord_interaction)
        else:
            await self.ivm.update(discord_interaction)
        return await super().callback(discord_interaction)


class Infinite_View_Manager:
    def __init__(
        self, cv: Custom_View[With_Options]
    ):
        self.last_selection:None|tuple[Option,...] = None
        self.first = True
        self.cv = cv
        self.max_select: int = (
            self.cv.sendable.max_selectable
            if self.cv.sendable.max_selectable is not None
            else len(self.cv.sendable.with_options)
        )
        if self.max_select > 1:
            logger.warn("Multiselections are not fully figured out with infinite selection. No way to clear responses.")
        self.min_select: int = (
            self.cv.sendable.min_selectable
            if self.cv.sendable.min_selectable is not None
            else 0
        )
        self.single_select = self.max_select == 1 and self.min_select == 1
        self.selected: int = 0
        self.total_options = len(self.cv.sendable.with_options)
        self.total_pages = ceil(self.total_options / MAX_OPTIONS_PER_SELECTABLE)
        self.page = 0
        self.selections: list[_Infinite_Selection] = []
        for p in range(self.total_pages):
            self.selections.append(_Infinite_Selection(self, p))
        self.left_button = discord.ui.Button(
            row=1,
            label="go left a page",
            emoji=LEFT_RIGHT_EMOJI[0]
        )

        async def left_button_press(interaction: discord.Interaction):
            self.page -= 1
            await self.update(interaction)

        self.left_button.callback = left_button_press
        self.right_button = discord.ui.Button(
            label= "go right a page",
            row=1,
            emoji=LEFT_RIGHT_EMOJI[1]
        )

        async def right_button_press(interaction: discord.Interaction):
            self.page += 1
            await self.update(interaction)

        self.right_button.callback = right_button_press
        self.confirm_button = discord.ui.Button(
            label="confirm selection",
            row=2,
        )

        async def confirm_press(interaction: discord.Interaction):
            await self.generate_interaction(interaction)

        self.confirm_button.callback = confirm_press

    async def generate_interaction(self, discord_interaction: discord.Interaction):
        options_selected: list[Option] = []
        for selection in self.selections:
            options_selected += list(selection.currently_selected)
        response = await self.cv.gi.interact(
            Interaction(
                at_address=self.cv.address,
                with_sendable=self.cv.sendable,
                by_player=self.cv.gi.find_player(discord_interaction.user.id),
                at_time=time(),
                content=Select_Options(
                    options=tuple(options_selected),
                    indices=tuple(
                        self.cv.sendable.with_options.index(option)
                        for option in options_selected
                    ),
                ),  # type:ignore
            )
        )
        self.last_selection = tuple(options_selected)
        self.cv.last_responses[Infinite_View_Manager] = response
        #reset in case wqe want to go again
        for selection in self.selections:
            selection.currently_selected = ()
            selection.number_selected = 0
        self.selected = 0
        await self.update(discord_interaction)

        #await self.cv.give_feedback(discord_interaction)

    async def update(self, discord_interaction:discord.Interaction):
        for selection in self.selections:
            selection.update()
        view = _Infinite_Select_View(self)
        text: str
        if self.single_select:
            text = "Please select an option."
        else:
            num_other = self.selected - self.selections[self.page].number_selected
            text = (
                f"Please select between {self.min_select} and {self.max_select} options, then press confirm.\n"
                + f"You have selected {num_other} option{s(num_other)} on other pages."
            )
        if self.last_selection is not None:
            text += f"\nLast time your submission was {wordify_iterable("'" + option.text + "'" for option in self.last_selection)}."
        if self.first:
            await discord_interaction.response.send_message(
                content=text,
                view=view,
                ephemeral=True
            )
            self.first = False
        else:
            await discord_interaction.response.edit_message(content=text, view=view)


class Infinite_Select_Button(discord.ui.Button):
    def __init__(self, cv: Custom_View[With_Options]):
        self.cv = cv
        super().__init__(label="Open dropdown", emoji=LIST)

    @override
    async def callback(self, discord_interaction: discord.Interaction):
        ivm = Infinite_View_Manager(self.cv)
        await ivm.update(discord_interaction)
        return await super().callback(discord_interaction)


class Infinite_Select_View(Custom_View):
    def __init__(
        self,
        gi: "Discord_Game_Interface",
        address: "Discord_Address",
        sendable: "With_Options",
    ):
        super().__init__(gi, address, sendable)
        self.add_item(Infinite_Select_Button(self))
