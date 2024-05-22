from typing import Generic, Mapping, Optional, override

from typing_extensions import TypeVar

from game import score_to_placement
from game.components.game_interface import Game_Interface
from game.game_bases.round_base import Rounds_Base
from game.game_bases.participant_base import Participant_Base
from utils.common import arg_fix_grouping, arg_fix_map
from utils.grammer import s
from utils.types import (
    Grouping,
    Number,
    Participant,
    Placement,
    PlayerId,
    PlayerPlacement,
)

PointType = TypeVar('PointType',bound = Number, default=int)

class Rounds_With_Points_Framework(Generic[Participant,PointType],Participant_Base[Participant],Rounds_Base):
    def __init__(self,gi:Game_Interface):
        Rounds_Base.__init__(self,gi)
        if Rounds_With_Points_Framework not in self.initialized_bases:
            self.initialized_bases.append(Rounds_With_Points_Framework)
            self.zero_score:PointType = 0#type: ignore
            self.num_rounds = 3
            self.point_word:str = "point"
            self.round_word:str = "round"
            self.reverse_points:bool = False
    @override
    def _configure_participants(self):
        self.point_totals:dict[Participant,PointType] = {
            participant:self.zero_score for participant in self._participants
        }
    async def announce_score(
            self,
            who:Optional[Participant|Grouping[Participant]] = None,
            amount:Optional[PointType|Mapping[Participant,PointType]] = None
            ):
        w = arg_fix_grouping(self._participants,who)
        if len(w) == 0:
            return
        a:Mapping[Participant,PointType] = arg_fix_map(w,self.zero_score,amount)
        participant_lines:list[str]
        if amount is None:
            participant_lines = list(
                f"{self._part_str(participant)} has {self.point_frmt(self.point_totals[participant])}" 
                for participant in w
            )
        else:
            participant_lines = list(
                f"{self._part_str(participant)} received {self.point_frmt(a[participant])} bringing them to " + 
                self.point_frmt(self.point_totals[participant] + a[participant])
                for participant in w
        )
        await self.basic_send('\n'.join(participant_lines))
    def point_frmt(self,num:Number) -> str:
        return f"{num} {self.point_word}{s(num)}"
    def receive_score(
            self,
            who:Optional[Participant|Grouping[Participant]] = None,
            amount:Optional[PointType|Mapping[Participant,PointType]] = None
            ):
        w = arg_fix_grouping(self._participants,who)
        a:Mapping[Participant,PointType] = arg_fix_map(w,self.zero_score,amount)
        for participant in w:
            self.point_totals[participant] += a[participant]#type: ignore
    async def announce_and_receive_score(
        self,
        who:Optional[Participant|Grouping[Participant]] = None,
        amount:Optional[PointType|Mapping[Participant,PointType]] = None
        ):
        await self.announce_score(who,amount)
        self.receive_score(who,amount)
    @override
    async def end_round(self):
        await self.announce_score()
    @override
    def _generate_participant_placements(self) -> Placement[Participant]:
        return score_to_placement(self.point_totals,self._participants,not self.reverse_points)


class Rounds_With_Points_Base(Rounds_With_Points_Framework[PlayerId,int]):
    def __init__(self,gi:Game_Interface):
        Rounds_With_Points_Framework.__init__(self,gi)
        if Rounds_With_Points_Base not in self.initialized_bases:
            self.initialized_bases.append(Rounds_With_Points_Base)
            self._participants = self.all_players
            self._part_str = lambda player: self.format_players([player])
    @override
    def generate_placements(self) -> PlayerPlacement:
        return self._generate_participant_placements()
    async def score(self,who:Optional[PlayerId|Grouping[PlayerId]] = None,
            amount:Optional[int|Mapping[PlayerId,int]] = None,
            mute:bool = False):
        if not mute:
            await self.announce_score(who,amount)
        self.receive_score(who,amount)