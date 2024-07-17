from typing import Optional, Unpack, TYPE_CHECKING

import utils.emoji_groups
from game.components.input_.response_validator import (
    ResponseValidator,
    default_text_validator,
    not_none,
)
from game.components.participant import Player, PlayerDictOptional, Players
from game.components.send import Address, MakeSendableArgs, Option, make_sendable
from game.components.send.interaction import (
    InteractionFilter,
    Select_Options,
    Send_Text,
    address_filter,
    all_filter,
    selection_limit_filter,
)
from game.components.send.sendable.sendables import Text_Only, Text_With_Text_Field, Text_With_Options
from smart_text import TextLike
from utils.common import arg_fix_grouping, get_first, no_filter

if TYPE_CHECKING:
    from game.components.game_interface import Game_Interface


class Interface_Component():
    def __init__(self,gi:'Game_Interface'):
        self.gi = gi
        self.im = self.gi.im
        self.sender = self.gi.get_sender()
        self.all_players:tuple[Player,...] = tuple(self.gi.get_players())
    async def _basic_text_response(
            self,
            content:str|Address,
            who_chooses:Optional[Player|Players] = None,
            interaction_filter:InteractionFilter[Send_Text] = no_filter, 
            allow_answer_change:bool = True,
            response_validator:ResponseValidator[Send_Text,Player] = default_text_validator) -> PlayerDictOptional[str]:
        wc:Players= arg_fix_grouping(self.all_players,who_chooses)
        address:Address
        if isinstance(content,Address):
            address = content
        else:
            question = Text_With_Text_Field(
                text = content
            )
            address = await self.sender(question)
        interaction_filter = all_filter(interaction_filter,address_filter(address))
        player_input = self.im.text(
            identifier = "this text question",
            participants=wc,
            interaction_filter=interaction_filter,
            allow_edits=allow_answer_change,
            response_validator=response_validator
        )
        await player_input.run()

        return {player:(
            None if player_input.responses[player] is None else player_input.responses[player].text#type:ignore
            ) for player in wc}
    async def _basic_multiple_choice(
            self,
            content:Optional[str|Address] = None,
            options:list[str] = [],
            who_chooses:Optional[Players|Player] = None,
            emojis:Optional[list[str]] = None, 
            interaction_filter:InteractionFilter[Select_Options] = no_filter, 
            allow_answer_change:bool = True, 
            response_validator:ResponseValidator[Select_Options,Player] = not_none) -> PlayerDictOptional[int]:
        wc:Players = arg_fix_grouping(self.all_players,who_chooses)
        address:Address
        if isinstance(content,Address):
            address = content
        else:
            emj:list[str] = []
            if emojis is None:
                emj += utils.emoji_groups.COLORED_CIRCLE_EMOJI
            else:
                emj += emojis
            bp:list[Option] = []
            for i in range(len(options)):
                split = options[i].split('-')
                if len(split) == 2:
                    text, long_text = split
                    text = text.strip()
                    long_text = long_text.strip()
                else:
                    text = options[i]
                    long_text = options[i]
                bp.append(
                    Option(
                        text = text,
                        emoji=emj[i],
                        long_text=long_text
                    )
                )
            question = Text_With_Options(
                text = "Please select an option:" if content is None else content,
                with_options=tuple(bp)
            )
            address = await self.sender(question)
        interaction_filter = all_filter(interaction_filter,address_filter(address),selection_limit_filter())
        player_input = self.im.select(
            identifier = "this single selection multiple choice question",
            participants=wc,
            interaction_filter=interaction_filter,
            allow_edits=allow_answer_change,
            response_validator=response_validator
        )
        await player_input.run()

        return {player:(
            None if player_input.responses[player] is None else get_first(player_input.responses[player])#type:ignore
        ) for player in wc}
    async def send(self,address:Address|None=None,**kwargs:Unpack[MakeSendableArgs]) -> Address:
        sendable = make_sendable(**kwargs)
        return await self.sender(sendable,address)
    async def say(self,text:TextLike,address:Address|None = None) -> Address:
        return await self.sender(
            Text_Only(text=text),
            address=address
        )