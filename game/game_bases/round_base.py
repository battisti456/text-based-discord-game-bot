from typing import Optional, override
import asyncio

from game.game import Game_Interface
from game.game_bases.participant_base import Participant_Base

from game.components.participant import ParticipantVar

class Rounds_Base(Participant_Base[ParticipantVar]):
    def __init__(self,gi:Game_Interface):
        Participant_Base.__init__(self,gi)#type:ignore
        if Rounds_Base not in self.initialized_bases:
            self.initialized_bases.append(Rounds_Base)
            self.num_rounds:Optional[int] = None
            """num_rounds to run for, if None run forever, if 1 it won't announce round number"""
            self.round_word:str = 'round'
            self.participant_round_is_concurrent:bool = True
    def string_round(self,round:int) -> str:
        return f"{self.round_word} {round}"
    async def core_round(self):
        if not self.participant_round_is_concurrent:
            for participant in self._participants:
                await self.participant_round(participant)
        else:
            tasks:list[asyncio.Task] = list(
                asyncio.create_task(self.participant_round(participant)) 
                for participant in self._participants
            )
            await asyncio.gather(*tasks)
    async def start_round(self):
        ...
    async def end_round(self):
        ...
    async def participant_round(self,participant:ParticipantVar):
        ...
    @override
    async def _run(self):
        round:int = 0
        of_str:str = ""
        if isinstance(self.num_rounds,int):
            of_str = f" of {self.num_rounds}"
        while True:
            if not self.num_rounds == 1:
                await self.say(f"## {self.string_round(round+1).capitalize()}{of_str}:")
            await self.start_round()
            await self.core_round()
            await self.end_round()
            round += 1
            if round == self.num_rounds:
                break
