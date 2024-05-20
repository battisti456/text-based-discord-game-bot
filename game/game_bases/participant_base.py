from typing import Generic, Callable, override

from game.game import Game, Game_Interface
from utils.types import Participant, Placement

class Participant_Base(Generic[Participant],Game):
    def __init__(self,gi:Game_Interface):
        Game.__init__(self,gi)
        if Participant_Base not in self.initialized_bases:
            self.initialized_bases.append(Participant_Base)
            self._part_str:Callable[[Participant],str] = lambda part: str(part)
            self._participants:tuple[Participant,...] = tuple()
            self._participant_name:str = "participant"
    def _configure_participants(self):
        ...
    def _generate_participant_placements(self) -> Placement[Participant]:
        ...
    @override
    async def game_setup(self):
        self._configure_participants()
        await super().game_setup()