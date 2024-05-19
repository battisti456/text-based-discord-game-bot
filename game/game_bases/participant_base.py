from typing import Generic, Callable, override

from game.game import Game, Game_Interface
from game.utils.types import Participant, Placement

class Participant_Base(Generic[Participant],Game):
    def __init__(self,gi:Game_Interface):
        Game.__init__(self,gi)
        if Participant_Base not in self.initialized_bases:
            self.initialized_bases.append(Participant_Base)
            self.part_str:Callable[[Participant],str] = lambda part: str(part)
            self.participants:tuple[Participant,...] = tuple()
            self.participant_name:str = "participant"
    def configure_participants(self):
        ...
    def generate_participant_placements(self) -> Placement[Participant]:
        ...
    @override
    async def game_setup(self):
        self.configure_participants()
        await super().game_setup()