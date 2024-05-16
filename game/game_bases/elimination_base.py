from game import PlayerId, PlayerDict, PlayerPlacement, Participant, GameEndException, Placement
from game.components.game_interface import Game_Interface
from game.game import Game, police_game_callable
from game.utils.common import Grouping, arg_fix_grouping
from game.utils.grammer import wordify_iterable

from typing import Generic, Callable

class EliminationGameEnd(GameEndException):
    ...

class Elimination_Framework(Generic[Participant],Game):
    def __init__(self,gi:Game_Interface):
        Game.__init__(self,gi)
        if not Elimination_Framework in self.initialized_bases:
            self.initialized_bases.append(Elimination_Framework)
            self.part_str:Callable[[Participant],str] = lambda part: str(part)
    def configure(self,participants:Grouping[Participant]):
        self.participants:tuple[Participant,...] = tuple(participants)
        self.elimination_order:Placement[Participant] = tuple()
    @property
    def eliminated(self) -> frozenset[Participant]:
        return frozenset(set().union(*(set(rank) for rank in self.elimination_order)))
    @property
    def not_eliminated(self) -> frozenset[Participant]:
        return frozenset(set(self.participants) - self.eliminated)
    async def announce_eliminate(self,participants:Grouping[Participant]|Participant):
        participants = arg_fix_grouping(self.participants,participants)
        to_eliminate:frozenset[Participant] = frozenset(participants) - frozenset(self.eliminated)
        num_left:int = len(self.not_eliminated)
        message_text:str = f"{wordify_iterable(map(self.part_str,to_eliminate))} "
        if len(to_eliminate) == num_left:
            message_text += "should have been eliminated, but as this would have taken out all of the remaining players, we will forgive them instead."
        elif len(to_eliminate) == num_left - 1:
            message_text += f"have been eliminated, leaving {self.part_str(tuple(set(self.not_eliminated) - to_eliminate)[0])} as the winner!"
        elif len(to_eliminate) == 1:
            message_text += "has been eliminated."
        else:
            message_text += "have been eliminated."
        await self.basic_send(message_text)
    def eliminate(self,participants:Grouping[Participant]|Participant):
        """
        attempts to eliminate participants; returns True if successful, False if not
        """
        participants = arg_fix_grouping(self.participants,participants)
        to_eliminate:frozenset[Participant] = frozenset(participants) - frozenset(self.eliminated)
        self.elimination_order += (tuple(to_eliminate),)
        if to_eliminate == set(self.not_eliminated):
            raise EliminationGameEnd()
    async def core_game(self):
        ...
    async def _run(self):
        try:
            while True:
                await self.core_game()
        except EliminationGameEnd:
            ...
    async def generate_participant_placements(self) -> Placement[Participant]:
        return self.elimination_order
        
class Elimination_Base(Elimination_Framework[PlayerId]):
    def __init__(self,gi:Game_Interface):
        Elimination_Framework.__init__(self,gi)
        if not Elimination_Base in self.initialized_bases:
            self.initialized_bases.append(Elimination_Base)
            self.configure(self.all_players)
            
            