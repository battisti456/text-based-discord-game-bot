from typing import TYPE_CHECKING, Any

import discord

from discord_interface.common import Discord_Address, f

if TYPE_CHECKING:
    from discord_interface.discord_interface import Discord_Game_Interface
    from game.components.send import  Response

class Custom_View[SendableType](discord.ui.View):
    def __init__(self,gi:'Discord_Game_Interface',address:'Discord_Address',sendable:SendableType):
        self.gi  = gi
        self.address = address
        self.sendable = sendable
        super().__init__(timeout=None)
        self.last_responses:dict[type[Any],tuple['Response',...]] = {}
        #disabled, it didn't really help all that much
        #self.add_item(Info_Button(self))
    async def give_feedback(self, discord_interaction: discord.Interaction):
        await discord_interaction.response.defer()
        return
        #disabled cause it didn't look great visually
        # if len(self.last_responses) == 0 or all(len(response_group) == 0  for response_group in self.last_responses.values()):
        #     await discord_interaction.response.defer()
        # else:
        #     await discord_interaction.response.send_message(
        #         content=self.summarize_responses(),
        #         ephemeral=True,
        #         delete_after=TIME_FEEDBACK_LASTS
        #     )
    def summarize_responses(self) -> str:
        return '\n'.join('\n'.join(f(response.to_text()) for response in response_group) for response_group in self.last_responses.values())