from typing import Optional, Unpack

import utils.emoji_groups
from game.components.game_interface import Game_Interface
from game.components.participant import Player, PlayerDictOptional, PlayersIds
from game.components.input_ import (
    Player_Single_Selection_Input,
    Player_Text_Input,
)
from game.components.input_.response_validator import (
    ResponseValidator,
    default_text_validator,
    not_none,
)
from game.components.send import Address, MakeSendableArgs, Option, make_sendable
from game.components.send.old_message import Old_Message
from game.components.send.sendable.sendables import Text_Only, Text_With_Text_Field
from smart_text import TextLike
from utils.common import arg_fix_grouping
from utils.types import (
    Grouping,
)


class Interface_Component():
    def __init__(self,gi:Game_Interface):
        self.gi = gi
        self.sender = self.gi.get_sender()
        self.all_players:tuple[Player,...] = tuple(self.gi.get_players())
    async def _basic_text_response(
            self,content:str,who_chooses:Optional[Player|PlayersIds] = None,
            channel_id:Optional[ChannelId] = None, allow_answer_change:bool = True,
            response_validator:ResponseValidator[str] = default_text_validator) -> PlayerDictOptional[str]:
        """
        sets up and runs a text input, returning its responses
        
        content: text to send in a message that will be replied to
        
        who_chooses: the list of players whose input matters, if None assumes self.players
        
        channel_id: what channel_id this message should be sent on

        allow_answer_change: weather or not users are permitted to change their response while the input is running
        """
        wc:PlayersIds= arg_fix_grouping(self.all_players,who_chooses)
        question = Text_With_Text_Field(
            text = content
        )
        question_address = await self.sender.generate_address(channel_id)
        await self.sender(question,question_address)
        player_input = Player_Text_Input(
            name = "this text question",
            gi = self.gi,
            sender = self.sender,
            players=wc,
            question_address=question_address,
            allow_edits=allow_answer_change,
            response_validator=response_validator
        )
        await player_input.run()

        return player_input.responses
    async def _basic_multiple_choice(
            self,content:Optional[str] = None,options:list[str] = [],who_chooses:Optional[PlayersIds|Player] = None,
            emojis:Optional[list[str]] = None, channel_id:Optional[ChannelId] = None, 
            allow_answer_change:bool = True, response_validator:ResponseValidator[int] = not_none) -> PlayerDictOptional[int]:
        """
        sets up and runs a multiple choice input, returning its responses
        
        content: text to send in a message that will be replied to
        
        options: the list of names of options that the players choose between
        
        who_chooses: the list of players whose input matters, if None assumes self.players
        
        emoji: the list of emoji symbols representing the choices, if None, defaults to colored circles
        
        channel_id: what channel_id this message should be sent on

        allow_answer_change: weather or not users are permitted to change their response while the input is running
        """
        wc:PlayersIds = arg_fix_grouping(self.all_players,who_chooses)
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
        question = Old_Message(
            text = content,
            on_channel=channel_id,
            with_options=bp
        )
        question_address = await self.sender(question)
        player_input = Player_Single_Selection_Input(
            name = "this single selection multiple choice question",
            gi = self.gi,
            sender = self.sender,
            players=wc,
            question_address=question_address,
            allow_edits=allow_answer_change,
            response_validator=response_validator
        )
        await player_input.run()

        return player_input.responses
    def format_players_md(self,players:Grouping[Player]) -> str:
            """
            returns the senders formatting of a list of players with markdown
            """
            return self.sender.format_players_md(players)
    def format_players(self,user_id:PlayersIds) -> str:
        """
        returns the senders formatting of a list of players without markdown
        """
        return self.sender.format_players(user_id)
    async def send(self,address:Address|None=None,**kwargs:Unpack[MakeSendableArgs]) -> Address:
        sendable = make_sendable(**kwargs)
        return await self.sender(sendable,address)
    async def say(self,text:TextLike,address:Address|None = None) -> Address:
        return await self.sender(
            Text_Only(text=text),
            address=address
        )