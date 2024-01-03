from game.game import Game, police_game_callable
from game.game_interface import Game_Interface
from game.message import Message, make_bullet_points
from game.player_input import Player_Single_Choice_Input, Player_Text_Input, run_inputs
from game.emoji_groups import COLORED_CIRCLE_EMOJI, NO_YES_EMOJI

from game import PlayerId,PlayerDict, PlayerDictOptional, make_player_dict
from typing import Optional, overload

class Basic_Secret_Message_Base(Game):
    def __init__(self,gi:Game_Interface):
        Game.__init__(self,gi)
        if not Basic_Secret_Message_Base in self.initialized_bases:
            self.initialized_bases.append(Basic_Secret_Message_Base)

    async def basic_secret_send(
            self,player:Optional[list[PlayerId]|PlayerId] = None,content:Optional[str|PlayerDict[str]] = None,
            attatchements_data:Optional[list[str]|PlayerDict[list[str]]] = None):
        p:list[PlayerId] = []
        if player is None:
            p = list(self.players)
        elif isinstance(player,list):
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
            ) -> str:
        ...
    @overload
    async def basic_secret_text_response(
            self,players:Optional[list[PlayerId]]=...,
            content:Optional[str|PlayerDict[str]]=..., allow_answer_change:bool=...,
            ) -> PlayerDict[str]:
        ...
    async def basic_secret_text_response(
            self,players:Optional[list[PlayerId]|PlayerId] = None,
            content:Optional[str|PlayerDict[str]] = None, allow_answer_change:bool = True,
            ) -> str|PlayerDict[str]:
        p:list[PlayerId] = []
        if players is None:
            p = list(self.players)
        elif isinstance(players,list):
            p = players
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
                "their secret text response",
                self.gi,
                self.sender,
                [player],
                who_can_see=[player],
                message=message,
                allow_edits=allow_answer_change
            )
            inputs[player] = inpt
        await run_inputs(
            list(inputs[player] for player in p),
            sender = self.sender)
        if players is None or isinstance(players,list):
            to_return_dict:PlayerDict[str] = {}
            for player in p:
                response = inputs[player].responses[player]
                assert not response is None
                to_return_dict[player] = response
            return to_return_dict
        else:
            to_return = inputs[players].responses[players]
            assert isinstance(to_return,str)
            return to_return
    @overload
    async def basic_secret_multiple_choice(
            self,players:PlayerId=...,
            content:Optional[str|PlayerDict[str]]=...,
            options:Optional[list[str]|PlayerDict[list[str]]]=...,
            emojis:Optional[list[str]|PlayerDict[list[str]]]=...,
            allow_answer_change:bool=...,
        ) -> int:
        ...  
    @overload
    async def basic_secret_multiple_choice(
            self,players:list[PlayerId]|None=...,
            content:Optional[str|PlayerDict[str]]=...,
            options:Optional[list[str]|PlayerDict[list[str]]]=...,
            emojis:Optional[list[str]|PlayerDict[list[str]]]=...,
            allow_answer_change:bool=True,
        ) -> PlayerDict[int]:
        ...
    async def basic_secret_multiple_choice(
            self,players:Optional[PlayerId|list[PlayerId]] = None,
            content:Optional[str|PlayerDict[str]] = None,
            options:Optional[list[str]|PlayerDict[list[str]]] = None,
            emojis:Optional[list[str]|PlayerDict[list[str]]] = None,
            allow_answer_change:bool=True,
        ) -> int|PlayerDict[int]:
        assert not options is None
        p:list[PlayerId] = []
        if players is None:
            p = list(self.players)
        elif isinstance(players,list):
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
        
        inputs:PlayerDict[Player_Single_Choice_Input] = {}
        for player in p:
            message= Message(
                content = c[player],
                players_who_can_see=[player],
                bullet_points=make_bullet_points(o[player],e[player])
            )
            inpt = Player_Single_Choice_Input(
                "their secret multiple choice response",
                self.gi,
                self.sender,
                [player],
                who_can_see=[player],
                message=message,
                allow_edits=allow_answer_change
            )
            inputs[player] = inpt
        await run_inputs(
            list(inputs[player] for player in p),
            sender = self.sender)
        if players is None or isinstance(players,list):
            to_return_dict:PlayerDict[int] = {}
            for player in p:
                response = inputs[player].responses[player]
                assert not response is None
                to_return_dict[player] = response
            return to_return_dict
        else:
            to_return = inputs[players].responses[players]
            assert isinstance(to_return,str)
            return to_return
    @overload
    async def basic_secret_no_yes(
            self,players:PlayerId=...,
            content:Optional[str|PlayerDict[str]]=...,
            allow_answer_change:bool=...,
            ) -> int:
        ...
    @overload
    async def basic_secret_no_yes(
            self,players:Optional[list[PlayerId]]=...,
            content:Optional[str|PlayerDict[str]]=...,
            allow_answer_change:bool=...,
            ) -> PlayerDict[int]:
        ...
    async def basic_secret_no_yes(
            self,players:Optional[PlayerId|list[PlayerId]] = None,
            content:Optional[str|PlayerDict[str]] = None,
            allow_answer_change:bool = True,
            ) -> int|PlayerDict[int]:
        return await self.basic_secret_multiple_choice(
            players,content,['no','yes'],list(NO_YES_EMOJI),allow_answer_change
        )