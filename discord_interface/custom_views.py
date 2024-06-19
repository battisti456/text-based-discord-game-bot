from time import time
from typing import TYPE_CHECKING,  override, Any

import discord

from discord_interface.common import f
from game.components.send import Interaction, Interaction_Content
from game.components.send.interaction import Select_Options, Send_Text
from game.components.send.sendable.prototype_sendables import (
    With_Options,
    With_Text_Field,
)
from utils.common import get_first

if TYPE_CHECKING:
    from discord_interface.common import Discord_Address
    from discord_interface.discord_interface import Discord_Game_Interface
    from game.components.send import Option, Response

INFO_TEXT = "Click here to view your feedback!"
TIME_FEEDBACK_LASTS = 30

class Info_Button(discord.ui.Button):
    def __init__(self,cv:'Custom_View'):
        self.cv = cv
        super().__init__(label=INFO_TEXT)
    @override
    async def callback(self, discord_interaction: discord.Interaction):
        await self.cv.give_feedback(discord_interaction)

class Custom_View[SendableType](discord.ui.View):
    def __init__(self,gi:'Discord_Game_Interface',address:'Discord_Address',sendable:SendableType):
        self.gi  = gi
        self.address = address
        self.sendable = sendable
        super().__init__(timeout=None)
        self.last_responses:dict[type[Any],'Response|None'] = {}
        self.add_item(Info_Button(self))
    async def give_feedback(self, discord_interaction: discord.Interaction):
        print(self.last_responses)
        if len(self.last_responses) == 0 or all(value is None for value in self.last_responses.values()):
            await discord_interaction.response.defer()
        else:
            await discord_interaction.response.send_message(
                content=self.summarize_responses(),
                ephemeral=True,
                delete_after=TIME_FEEDBACK_LASTS
            )
    def summarize_responses(self) -> str:
        return '\n'.join(f(response.to_text()) for response in self.last_responses.values() if response is not None)


class Interaction_Handler():
    def __init__(self,cv:Custom_View):
        self.cv = cv
    async def handle_interaction(self,discord_interaction:discord.Interaction,content:Interaction_Content):
        assert discord_interaction.data is not None
        response = await self.cv.gi.interact(Interaction(
            at_address=self.cv.address,
            with_sendable=self.cv.sendable,
            by_player=discord_interaction.user.id,#type:ignore
            at_time=time(),
            content = content
        ))
        self.cv.last_responses[Interaction_Handler] = response
        await self.cv.give_feedback(discord_interaction)

class Select(discord.ui.Select,Interaction_Handler):
    def __init__(self,cv:Custom_View[With_Options]):
        self.cv = cv
        Interaction_Handler.__init__(self,cv)
        self.game_discord_option_map:'dict[Option,discord.SelectOption]' = {
            option:discord.SelectOption(
                label = option.text,
                emoji= option.emoji,
                description=option.long_text
            ) for option in self.cv.sendable.with_options
        }
        kwargs = {}
        if self.cv.sendable.min_selectable is not None:
            kwargs['min_values'] = self.cv.sendable.min_selectable
        if self.cv.sendable.max_selectable is not None:
            kwargs['max_values'] = self.cv.sendable.max_selectable
        discord.ui.Select.__init__(self,#could add placeholder
            options = list(self.game_discord_option_map[option] for option in self.cv.sendable.with_options),
            **kwargs
        )
    @override
    async def callback(self, discord_interaction: 'discord.Interaction'):
        print(discord_interaction.data)
        options:tuple[Option,...] = tuple(
            get_first(option for option in self.cv.sendable.with_options if option.text == value) for 
            value in discord_interaction.data['values']#type:ignore
        )
        indices:tuple[int,...] = tuple(
            self.cv.sendable.with_options.index(option) for option in options
        )
        await self.handle_interaction(discord_interaction,Select_Options(
                options,
                indices
            ))
def hint_text(sendable:'With_Text_Field') -> str:
    return "Input your response here!" if sendable.hint_text is None else f(sendable.hint_text)
class One_Selectable_View(Custom_View):
    def __init__(self,gi:'Discord_Game_Interface',address:'Discord_Address',sendable:'With_Options'):
        super().__init__(gi,address,sendable)
        self.add_item(Select(self))

class Text_Input(discord.ui.TextInput):
    def __init__(self,cv:Custom_View[With_Text_Field]):
        self.cv = cv
        super().__init__(label = hint_text(self.cv.sendable))

class Text_Input_Modal(discord.ui.Modal,Interaction_Handler):
    def __init__(self,cv:Custom_View):
        super().__init__(title="Input text here:")
        Interaction_Handler.__init__(self,cv)
        self.add_item(Text_Input(cv))
    @override
    async def on_submit(self, discord_interaction: discord.Interaction):
        await self.handle_interaction(discord_interaction,Send_Text(
                discord_interaction.data['components'][0]['components'][0]['value']#type:ignore
            ))


class Text_Input_Button(discord.ui.Button):
    def __init__(self,cv:Custom_View[With_Text_Field]):
        self.cv = cv
        super().__init__(label=hint_text(self.cv.sendable))
    @override
    async def callback(self, discord_interaction: discord.Interaction):
        await discord_interaction.response.send_modal(Text_Input_Modal(self.cv))
        return await super().callback(discord_interaction)


class One_Text_Field_View(Custom_View):
    def __init__(self,gi:'Discord_Game_Interface',address:'Discord_Address',sendable:'With_Text_Field'):
        super().__init__(gi,address,sendable)
        self.add_item(Text_Input_Button(self))

class Options_And_Text_View(Custom_View):
    def __init__(self,gi:'Discord_Game_Interface',address:'Discord_Address',sendable:'With_Text_Field'):
        super().__init__(gi,address,sendable)
        self.add_item(Text_Input_Button(self))
        self.add_item(Select(self))