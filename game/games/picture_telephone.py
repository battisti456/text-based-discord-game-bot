from typing import override

from game.components.game_interface import Game_Interface
from game.components.message import Message
from game.components.player_input import Player_Text_Input, run_inputs
from game.components.response_validator import text_validator_maker
from game.game_bases import Image_Search_Base, Rounds_With_Points_Base
from utils.types import PlayerDict, PlayerDictOptional, PlayerId

NUM_ROUNDS = 1
MIN_NUM_WORDS = 1
MAX_NUM_WORDS = 5

validator = text_validator_maker(
    min_num_words=MIN_NUM_WORDS,
    max_num_words=MAX_NUM_WORDS,
    is_alpha=True
)

class Picture_Telephone(Rounds_With_Points_Base, Image_Search_Base):
    def __init__(self,gi:Game_Interface):
        raise NotImplementedError()
        Rounds_With_Points_Base.__init__(self,gi)
        Image_Search_Base.__init__(self,gi)
        self.num_rounds = NUM_ROUNDS
        self._texts:list[PlayerDict[str]]
        self._images:list[PlayerDict[str]]
        self.failed_paths:set[int]
        self.current_offset = 0
    @property
    def texts(self) -> list[PlayerDict[str]]:
        return list(self._texts[i] for i in range(len(self._texts)) if i not in self.failed_paths)
    @property
    def images(self) -> list[PlayerDict[str]]:
        return list(self._texts[i] for i in range(len(self._images)) if i not in self.failed_paths)
    def reset(self):
        self._texts = []
        self._images = []
        self.failed_paths = set()
        self.current_offset = 0
    @override
    async def game_intro(self):
        pass
    @override
    async def core_game(self) -> PlayerDict[int] | None:
        self.reset()
        while self.current_offset < len(self.unkicked_players):
            await self.prompt_telephone()
            self.current_offset += 1
        for i in range(len(self.all_players)):
            if i not in self.failed_paths:
                ...#wait does this game even make sense?
    def i(self,player:PlayerId,add:int = 0) -> int:
        return (self.unkicked_players.index(player)+self.current_offset+add)%len(self.images)
    async def prompt_telephone(self):
        questions:PlayerDict[Message] = {}
        inputs:PlayerDict[Player_Text_Input] = {}
        for player in self.unkicked_players:
            content:str =""
            attach_paths:list[str]|None = None
            if len(self.images[0]) == 0:
                content = f"Please enter between {MIN_NUM_WORDS} and {MAX_NUM_WORDS} words."
            else:
                attach_paths = [self.images[self.i(player,-1)][player]]
                content = f"Please summerize this image in between {MIN_NUM_WORDS} and {MAX_NUM_WORDS} words."
            questions[player] = Message(
                content = content,
                attach_paths=attach_paths,
                players_who_can_see=[player]
            )
            inputs[player] = Player_Text_Input(
                name = f"{self.sender.format_players_md([player])}",
                gi = self.gi,
                sender = self.sender,
                players = [player],
                who_can_see=[player],
                message=questions[player],
                response_validator= validator
            )
        await run_inputs(list(inputs[player] for player in self.unkicked_players))
        raw_text_responses:PlayerDictOptional[str] = {player:inputs[player].responses[player] for player in self.unkicked_players}
        none_responders:list[PlayerId] = list(player for player in self.unkicked_players if raw_text_responses[player] is None)
        failed_i = set(self.i(player) for player in none_responders)
        failed_paths = set(list(j for j in range(len(self._texts)) if self.images[i] == self._images[j])[0] for i in failed_i)
        self.failed_paths = self.failed_paths.union(failed_paths)
        await self.kick_players(none_responders,'timeout')
        text_responses:PlayerDict[str] = self.clean_player_dict(raw_text_responses)
        for player in self.unkicked_players:
            i = self.i(player)
            self.texts[i][player] = text_responses[player]
            self.images[i][player] = self.temp_random_image(search_terms=text_responses[player].split())


