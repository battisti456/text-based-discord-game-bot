from typing import Iterable, Optional, overload

from game import make_player_dict
from game.components.game_interface import Game_Interface
from game.components.message import Message, make_bullet_points
from game.components.player_input import (
    Player_Single_Selection_Input,
    Player_Text_Input,
    run_inputs,
)
from game.components.response_validator import ResponseValidator, not_none
from game.game import Game
from utils.emoji_groups import COLORED_CIRCLE_EMOJI, NO_YES_EMOJI
from utils.types import PlayerDict, PlayerDictOptional, PlayerId, Grouping


class Basic_Secret_Message_Base(Game):
    def __init__(self,gi:Game_Interface):
        Game.__init__(self,gi)
        if Basic_Secret_Message_Base not in self.initialized_bases:
            self.initialized_bases.append(Basic_Secret_Message_Base)

    async def basic_secret_send(
            self,player:Optional[Iterable[PlayerId]|PlayerId] = None,content:Optional[str|PlayerDict[str]] = None,
            attatchements_data:Optional[list[str]|PlayerDict[list[str]]] = None):
        p:Iterable[PlayerId] = []
        if player is None:
            p = self.unkicked_players
        elif isinstance(player,Iterable):
            p = player
        else:
            p = [player]
        c:PlayerDict[str] = {}
        if isinstance(content,dict):
            c = content
        elif isinstance(content,str):
            c = make_player_dict(p,content)
        a:PlayerDict[list[str]] = make_player_dict(p,[])
        if isinstance(attatchements_data,list):
            a = make_player_dict(p,attatchements_data)
        elif isinstance(attatchements_data,dict):
            a = attatchements_data
        for pl in p:
            message = Message(c[pl],a[pl],players_who_can_see=[pl])
            await self.sender(message)
    @overload
    async def basic_secret_text_response(self,players:PlayerId=...,
            content:Optional[str|PlayerDict[str]]=..., allow_answer_change:bool=...,
            response_validator:ResponseValidator[str]=...) -> str:
        ...
    @overload
    async def basic_secret_text_response(
            self,players:Optional[Iterable[PlayerId]]=...,
            content:Optional[str|PlayerDict[str]]=..., allow_answer_change:bool=...,
            response_validator:ResponseValidator[str]=...) -> PlayerDict[str]:
        ...
    async def basic_secret_text_response(
            self,players:Optional[Iterable[PlayerId]|PlayerId] = None,
            content:Optional[str|PlayerDict[str]] = None, allow_answer_change:bool = True,
            response_validator:ResponseValidator[str] = not_none) -> str|PlayerDict[str]:
        p:Iterable[PlayerId] = []
        if players is None:
            p = self.unkicked_players
        elif isinstance(players,Iterable):
            p = list(players)
        else:
            p = [players]
        c:PlayerDict[str] = {}
        if isinstance(content,dict):
            c = content
        elif isinstance(content,str):
            c = make_player_dict(p,content)
        inputs:PlayerDict[Player_Text_Input] = {}
        for player in p:
            message= Message(
                content = c[player],
                players_who_can_see=[player]
            )
            inpt = Player_Text_Input(
                f"{self.format_players([player])}'s secret text response",
                self.gi,
                self.sender,
                [player],
                who_can_see=[player],
                message=message,
                allow_edits=allow_answer_change,
                response_validator=response_validator
            )
            inputs[player] = inpt
        await run_inputs(
            list(inputs[player] for player in p),
            sender = self.sender,
            basic_feedback=True,
            completion_sets=[set(inputs.values())])
        raw_responses:PlayerDictOptional[str] = {
            player:inputs[player].responses[player] for player in p
        }
        await self.kick_none_response(raw_responses)
        responses:PlayerDict[str] = self.clean_player_dict(raw_responses)
        if players is None or isinstance(players,Grouping):
            return responses
        else:
            if players in responses:
                return responses[player]
            else:
                return ""
    @overload
    async def basic_secret_multiple_choice(
            self,players:PlayerId=...,
            content:Optional[str|PlayerDict[str]]=...,
            options:Optional[list[str]|PlayerDict[list[str]]]=...,
            emojis:Optional[list[str]|PlayerDict[list[str]]]=...,
            allow_answer_change:bool=...,
            response_validator:ResponseValidator[int]=...
        ) -> int:
        ...  
    @overload
    async def basic_secret_multiple_choice(
            self,players:Iterable[PlayerId]|None=...,
            content:Optional[str|PlayerDict[str]]=...,
            options:Optional[list[str]|PlayerDict[list[str]]]=...,
            emojis:Optional[list[str]|PlayerDict[list[str]]]=...,
            allow_answer_change:bool=True,
            response_validator:ResponseValidator[int]=...
        ) -> PlayerDict[int]:
        ...
    async def basic_secret_multiple_choice(
            self,players:Optional[PlayerId|Iterable[PlayerId]] = None,
            content:Optional[str|PlayerDict[str]] = None,
            options:Optional[list[str]|PlayerDict[list[str]]] = None,
            emojis:Optional[list[str]|PlayerDict[list[str]]] = None,
            allow_answer_change:bool=True,
            response_validator:ResponseValidator[int] = not_none
        ) -> int|PlayerDict[int]:
        assert options is not None
        p:Iterable[PlayerId] = []
        if players is None:
            p = self.unkicked_players
        elif isinstance(players,Iterable):
            p = players
        else:
            p = [players]
        c:PlayerDict[str] = {}
        if isinstance(content,dict):
            c = content
        elif isinstance(content,str):
            c = make_player_dict(p,content)
        o:PlayerDict[list[str]] = {}
        if isinstance(options,list):
            o = make_player_dict(p,options)
        elif isinstance(options,dict):
            o = options
        e:PlayerDict[list[str]] = {}
        if isinstance(emojis,list):
            e = make_player_dict(p,emojis)
        elif emojis is None:
            e = make_player_dict(p,list(COLORED_CIRCLE_EMOJI))
        else:
            e = emojis
        
        inputs:PlayerDict[Player_Single_Selection_Input] = {}
        for player in p:
            message= Message(
                content = c[player],
                players_who_can_see=[player],
                bullet_points=make_bullet_points(o[player],e[player])
            )
            inpt = Player_Single_Selection_Input(
                "their secret multiple choice response",
                self.gi,
                self.sender,
                [player],
                who_can_see=[player],
                message=message,
                allow_edits=allow_answer_change,
                response_validator=response_validator
            )
            inputs[player] = inpt
        await run_inputs(
            list(inputs[player] for player in p),
            sender = self.sender,
            basic_feedback=True)
        raw_responses:PlayerDictOptional[int] = {
            player:inputs[player].responses[player] for player in p
        }
        await self.kick_none_response(raw_responses)
        responses:PlayerDict[int] = self.clean_player_dict(raw_responses)
        if players is None or isinstance(players,list):
            return responses
        else:
            if players in responses:
                return responses[player]
            else:
                return -1
    @overload
    async def basic_secret_no_yes(
            self,players:PlayerId=...,
            content:Optional[str|PlayerDict[str]]=...,
            allow_answer_change:bool=...,
            ) -> int:
        ...
    @overload
    async def basic_secret_no_yes(
            self,players:Optional[Iterable[PlayerId]]=...,
            content:Optional[str|PlayerDict[str]]=...,
            allow_answer_change:bool=...,
            ) -> PlayerDict[int]:
        ...
    async def basic_secret_no_yes(
            self,players:Optional[PlayerId|Iterable[PlayerId]] = None,
            content:Optional[str|PlayerDict[str]] = None,
            allow_answer_change:bool = True,
            ) -> int|PlayerDict[int]:
        return await self.basic_secret_multiple_choice(
            players,content,['no','yes'],list(NO_YES_EMOJI),allow_answer_change
        )