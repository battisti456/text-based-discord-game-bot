from typing import override

from game.components.game_interface import Game_Interface
from game.components.send.sendable.sendables import Text_Only
from game.components.player_input import Player_Text_Input
from game.components.response_validator import text_validator_maker
from game.game_bases import Rounds_With_Points_Base
from utils.emoji_groups import NUMBERED_KEYCAP_EMOJI
from utils.grammar import s
from utils.types import PlayerDict

validator = text_validator_maker(
    is_digit=True
)

class Basic_Game(Rounds_With_Points_Base):
    def __init__(self,gi:Game_Interface):
        Rounds_With_Points_Base.__init__(self,gi)
    @override
    async def game_intro(self):
        await self.say(
            "# Hi welcome to this basic game!\n" +
            "Answer with how many points you would like to get!"
        )
    @override
    async def core_round(self):
        question_address = await self.sender(Text_Only(text = "Respond here with how many points you would like!"))
        inpt = Player_Text_Input(
            "this point score question",
            self.gi,
            self.sender,
            self.unkicked_players,
            response_validator=validator,
            question_address=question_address
        )
        await inpt.run()
        await self.kick_none_response(inpt)
        responses:PlayerDict[str] = self.clean_player_dict(inpt.responses)

        await self.score(
            self.unkicked_players,
            {player:int(responses[player]) for player in self.unkicked_players}
        )

        return
        responses:PlayerDict[int] = await self.basic_multiple_choice(
            "Answer with how many points you would like to get!",
            list(str(num)+ " point" + s(num) for num in range(1,11)),
            emojis=list(NUMBERED_KEYCAP_EMOJI[1:])
        )#type: ignore

        await self.score(
            self.unkicked_players,
            {player:responses[player] + 1 for player in self.unkicked_players}
            )
        
