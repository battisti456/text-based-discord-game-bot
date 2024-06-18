from time import time
from typing import TYPE_CHECKING,  override

import discord

from discord_interface.common import f
from game.components.send import Interaction, Interaction_Content, Sendable
from game.components.send.interaction import Select_Options, Send_Text
from game.components.send.sendable.prototype_sendables import (
    With_Options,
    With_Text_Field,
)
from utils.common import get_first

if TYPE_CHECKING:
    from discord_interface.common import Discord_Address
    from discord_interface.discord_interface import Discord_Game_Interface
    from game.components.send import Option
    from smart_text import TextLike

class Custom_View(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

class Interaction_Handler():
    def __init__(self,gi:'Discord_Game_Interface',address:'Discord_Address',sendable:'Sendable'):
        self.gi = gi
        self.address = address
        self.sendable = sendable
    async def handle_interaction(self,discord_interaction:discord.Interaction,content:Interaction_Content):
        assert discord_interaction.data is not None
        response = await self.gi.interact(Interaction(
            at_address=self.address,
            with_sendable=self.sendable,
            by_player=discord_interaction.user.id,#type:ignore
            at_time=time(),
            content = content
        ))
        if response is None:
            await discord_interaction.response.defer()
        else:
            text:'TextLike' = ""
            if response.text is not None:
                text = response.text
            else:
                text = "This interaction has been " + ("rejected" if response.reject_interaction else "accepted") + "."
            await discord_interaction.response.send_message(
                content = f(text),
                ephemeral=True,
            )

class Select(discord.ui.Select,Interaction_Handler):
    def __init__(self,gi:'Discord_Game_Interface',address:'Discord_Address',sendable:'With_Options'):
        Interaction_Handler.__init__(self,gi,address,sendable)
        self.game_discord_option_map:'dict[Option,discord.SelectOption]' = {
            option:discord.SelectOption(
                label = option.text,
                emoji= option.emoji,
                description=option.long_text
            ) for option in sendable.with_options
        }
        kwargs = {}
        if sendable.min_selectable is not None:
            kwargs['min_values'] = sendable.min_selectable
        if sendable.max_selectable is not None:
            kwargs['max_values'] = sendable.max_selectable
        discord.ui.Select.__init__(self,#could add placeholder
            options = list(self.game_discord_option_map[option] for option in sendable.with_options),
            **kwargs
        )
    @override
    async def callback(self, discord_interaction: 'discord.Interaction'):
        assert isinstance(self.sendable,With_Options)
        await self.handle_interaction(discord_interaction,Select_Options(
                tuple(
                    get_first(option for option in self.sendable.with_options if option.text == value) for 
                    value in discord_interaction.data['values']#type:ignore
                )
            ))
def hint_text(sendable:'With_Text_Field') -> str:
    return "Input your response here!" if sendable.hint_text is None else f(sendable.hint_text)
class One_Selectable_View(Custom_View):
    def __init__(self,gi:'Discord_Game_Interface',address:'Discord_Address',sendable:'With_Options'):
        super().__init__()
        self.add_item(Select(gi,address,sendable))

class Text_Input(discord.ui.TextInput):
    def __init__(self,gi:'Discord_Game_Interface',address:'Discord_Address',sendable:'With_Text_Field'):
        self.gi = gi
        self.address = address
        self.sendable = sendable
        super().__init__(label = hint_text(sendable))

class Text_Input_Modal(discord.ui.Modal,Interaction_Handler):
    def __init__(self,gi:'Discord_Game_Interface',address:'Discord_Address',sendable:'With_Text_Field'):
        super().__init__(title="Input text here:")
        Interaction_Handler.__init__(self,gi,address,sendable)
        self.add_item(Text_Input(gi,address,sendable))
    @override
    async def on_submit(self, discord_interaction: discord.Interaction):
        await self.handle_interaction(discord_interaction,Send_Text(
                discord_interaction.data['components'][0]['components'][0]['value']#type:ignore
            ))


class Text_Input_Button(discord.ui.Button):
    def __init__(self,gi:'Discord_Game_Interface',address:'Discord_Address',sendable:'With_Text_Field'):
        self.gi = gi
        self.address = address
        self.sendable = sendable
        super().__init__(label=hint_text(sendable))
    @override
    async def callback(self, discord_interaction: discord.Interaction):
        await discord_interaction.response.send_modal(Text_Input_Modal(self.gi,self.address,self.sendable))
        return await super().callback(discord_interaction)


class One_Text_Field_View(Custom_View):
    def __init__(self,gi:'Discord_Game_Interface',address:'Discord_Address',sendable:'With_Text_Field'):
        super().__init__()
        self.add_item(Text_Input_Button(gi,address,sendable))