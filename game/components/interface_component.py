from typing import Iterable, Optional

from game import PlayerId, ChannelId, PlayerDictOptional
from game.components.game_interface import Game_Interface
from game.components.message import Message, Bullet_Point
from game.components.player_input import Player_Single_Selection_Input, Player_Text_Input
import game.utils.emoji_groups

class Interface_Component():
    def __init__(self,gi:Game_Interface):
        self.gi = gi
        self.sender = self.gi.get_sender()
        self.all_players:list[PlayerId] = self.gi.get_players()
    async def _basic_text_response(
            self,content:str,who_chooses:PlayerId|list[PlayerId]|None = None,
            channel_id:Optional[ChannelId] = None, allow_answer_change:bool = True) -> PlayerDictOptional[str]:
        """
        sets up and runs a text input, returning its responses
        
        content: text to send in a message that will be replied to
        
        who_chooses: the list of players whose input matters, if None assumes self.players
        
        channel_id: what channel_id this message should be sent on

        allow_answer_change: weather or not users are permitted to change their response while the input is running
        """
        wc:list[PlayerId] = []
        if isinstance(who_chooses,list):
            wc += who_chooses
        elif who_chooses is None:
            wc += self.all_players
        emj:list[str] = []
        question = Message(
            content = content,
            channel_id=channel_id
        )
        await self.sender(question)
        player_input = Player_Text_Input(
            name = "this text question",
            gi = self.gi,
            sender = self.sender,
            players=wc,
            message = question,
            allow_edits=allow_answer_change
        )
        await player_input.run()

        return player_input.responses
    async def _basic_multiple_choice(
            self,content:Optional[str] = None,options:list[str] = [],who_chooses:Optional[list[PlayerId]] = None,
            emojis:Optional[list[str]] = None, channel_id:Optional[ChannelId] = None, 
            allow_answer_change:bool = True) -> PlayerDictOptional[int]:
        """
        sets up and runs a multiple choice input, returning its responses
        
        content: text to send in a message that will be replied to
        
        options: the list of names of options that the players choose between
        
        who_chooses: the list of players whose input matters, if None assumes self.players
        
        emoji: the list of emoji symbols representing the choices, if None, defaults to colored circles
        
        channel_id: what channel_id this message should be sent on

        allow_answer_change: weather or not users are permitted to change their response while the input is running
        """
        wc:list[PlayerId] = []
        if isinstance(who_chooses,list):
            wc += who_chooses
        elif who_chooses is None:
            wc += self.all_players
        emj:list[str] = []
        if emojis is None:
            emj += game.utils.emoji_groups.COLORED_CIRCLE_EMOJI
        else:
            emj += emojis
        bp:list[Bullet_Point] = []
        for i in range(len(options)):
            bp.append(
                Bullet_Point(
                    text = options[i],
                    emoji=emj[i]
                )
            )
        question = Message(
            content = content,
            channel_id=channel_id,
            bullet_points=bp
        )
        await self.sender(question)
        player_input = Player_Single_Selection_Input(
            name = "this single selection multiple choice question",
            gi = self.gi,
            sender = self.sender,
            players=wc,
            message = question,
            allow_edits=allow_answer_change
        )
        await player_input.run()

        return player_input.responses
    def format_players_md(self,players:Iterable[PlayerId]) -> str:
            """
            returns the senders fomatting of a list of players with markdown
            """
            return self.sender.format_players_md(players)
    def format_players(self,user_id:list[PlayerId]) -> str:
        """
        returns the senders formatting of a list of players without markdown
        """
        return self.sender.format_players(user_id)
    async def basic_send(self,content:Optional[str] = None,attatchements_data:list[str] = [],
                   channel_id:Optional[ChannelId] = None):
        """
        creates a message with the given parameters and sends it with self.sender
        
        content: the text content of the message
        
        attatchements_data: a list of file paths to attatch to the message
        
        channel_id: what channel to send the message on
        """
        message = Message(
            content = content,
            attach_paths=attatchements_data,
            channel_id=channel_id
        )
        await self.sender(message)
    async def send(self,message:Message):
        """
        a wrapper of self.sender.__call__, for sending Message objects
        """
        await self.sender(message)
