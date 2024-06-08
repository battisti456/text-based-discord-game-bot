from typing import Optional, override

from game.components.game_interface import Game_Interface
from game.game_bases.round_base import Rounds_Base
from game.game_bases.participant_base import Participant_Base
from utils.common import arg_fix_grouping
from utils.exceptions import GameEndException
from utils.grammar import wordify_iterable
from utils.types import (
    Grouping,
    KickReason,
    Participant,
    Placement,
    PlayerId,
    PlayerPlacement,
)


class EliminationGameEnd(GameEndException):
    ...

class Elimination_Framework(Participant_Base[Participant],Rounds_Base):
    def __init__(self,gi:Game_Interface):
        Rounds_Base.__init__(self,gi)
        if Elimination_Framework not in self.initialized_bases:
            self.initialized_bases.append(Elimination_Framework)
    @override
    def _configure_participants(self):
        self.elimination_order:Placement[Participant] = tuple()
    @property
    def eliminated(self) -> frozenset[Participant]:
        return frozenset(set().union(*(set(rank) for rank in self.elimination_order)))
    @property
    def not_eliminated(self) -> frozenset[Participant]:
        return frozenset(self._participants) - self.eliminated
    async def announce_eliminate(self,participants:Grouping[Participant]|Participant):
        participants = arg_fix_grouping(self._participants,participants)
        to_eliminate:frozenset[Participant] = frozenset(participants) - frozenset(self.eliminated)
        num_left:int = len(self.not_eliminated)
        message_text:str = f"{wordify_iterable(map(self._part_str,to_eliminate))} "
        if len(to_eliminate) == 0:
            return
        if len(to_eliminate) == num_left:
            message_text += "should have been eliminated, but as this would have taken out all of the remaining players, we will forgive them instead"
            to_eliminate = frozenset()
        elif len(to_eliminate) == 1:
            message_text += "has been eliminated"
        else:
            message_text += "have been eliminated"
        if len(to_eliminate) == num_left -1:
            message_text += f", leaving {self._part_str(tuple(set(self.not_eliminated) - to_eliminate)[0])} as the winner!"
        else:
            message_text += '.'
        await self.basic_send(message_text)
    def eliminate_participants(self,participants:Grouping[Participant]|Participant):
        """
        attempts to eliminate participants; returns True if successful, False if not
        """
        participants = arg_fix_grouping(self._participants,participants)
        to_eliminate:frozenset[Participant] = frozenset(participants) - frozenset(self.eliminated)
        if not to_eliminate == set(self.not_eliminated) and len(to_eliminate) > 0:
            self.elimination_order += (tuple(to_eliminate),)
        if len(self.not_eliminated) == 1:
            raise EliminationGameEnd(f"all but one {self._participant_name} being eliminated")
    @override
    def _generate_participant_placements(self) -> Placement[Participant]:
        return tuple(reversed(self.elimination_order))
        
class Elimination_Base(Elimination_Framework[PlayerId]):
    def __init__(self,gi:Game_Interface):
        Elimination_Framework.__init__(self,gi)
        if Elimination_Base not in self.initialized_bases:
            self.initialized_bases.append(Elimination_Base)
            self._part_str = lambda player: self.sender.format_players((player,))
            self._participant_name = "player"
            self._participants = self.all_players
    async def eliminate(self,players:PlayerId|Grouping[PlayerId]):
        players = arg_fix_grouping(self.unkicked_players,players)
        await self.announce_eliminate(players)
        self.eliminate_participants(players)
        await super().kick_players(players, 'eliminated')
    @override
    async def kick_players(self, players: Grouping[PlayerId], reason: KickReason = 'unspecified', priority:Optional[int] = None):
        players = tuple(players)
        await super().kick_players(players, reason, priority)
        await self.announce_eliminate(players)
        self.eliminate_participants(players)
    @override
    def generate_placements(self) -> PlayerPlacement:
        print(self._generate_participant_placements())
        return (tuple(self.not_eliminated),) + self._generate_participant_placements()
            
            