from game.game import Game
from game.components.game_interface import Game_Interface
from game.utils.grammer import s
from game import PlayerId, PlayerPlacement, score_to_placement, Participant, Placement
from typing import Optional, Generic, Mapping, Callable, Iterable
from typing_extensions import TypeVar
from game.utils.common import arg_fix_map, Number, arg_fix_iterable

PointType = TypeVar('PointType',bound = Number, default=int)

class Rounds_With_Points_Framework(Generic[Participant,PointType],Game):
    def __init__(self,gi:Game_Interface):
        Game.__init__(self,gi)
        if not Rounds_With_Points_Framework in self.initialized_bases:
            self.initialized_bases.append(Rounds_With_Points_Framework)
            self.zero_score:PointType = 0#type: ignore
            self.num_rounds:int = 3
            self.point_word:str = "point"
            self.round_word:str = "round"
            self.reverse_points:bool = False
            self.part_str:Callable[[Participant],str] = lambda part: str(part)
    def configure(self,participants:Iterable[Participant]):
        self.participants:tuple[Participant,...] = tuple(participants)
        self.point_totals:dict[Participant,PointType] = {
            participant:self.zero_score for participant in self.participants
        }
    async def announce_score(
            self,
            who:Optional[Participant|Iterable[Participant]] = None,
            amount:Optional[PointType|Mapping[Participant,PointType]] = None
            ):
        w = arg_fix_iterable(self.participants,who)
        a:Mapping[Participant,PointType] = arg_fix_map(w,self.zero_score,amount)
        participant_lines:list[str]
        if amount is None:
            participant_lines = list(
                f"{self.part_str(participant)} has {self.point_frmt(self.point_totals[participant])}" 
                for participant in w
            )
        else:
            participant_lines = list(
                f"{self.part_str(participant)} received {self.point_frmt(a[participant])} bringing them to " + 
                self.point_frmt(self.point_totals[participant] + a[participant])
                for participant in w
        )
        await self.basic_send('\n'.join(participant_lines))
    def point_frmt(self,num:Number) -> str:
        return f"{num} {self.point_word}{s(num)}"
    def receive_score(
            self,
            who:Optional[Participant|Iterable[Participant]] = None,
            amount:Optional[PointType|Mapping[Participant,PointType]] = None
            ):
        w = arg_fix_iterable(self.participants,who)
        a:Mapping[Participant,PointType] = arg_fix_map(w,self.zero_score,amount)
        for participant in w:
            self.point_totals[participant] += a[participant]#type: ignore
    async def announce_and_receive_score(
        self,
        who:Optional[Participant|Iterable[Participant]] = None,
        amount:Optional[PointType|Mapping[Participant,PointType]] = None
        ):
        await self.announce_score(who,amount)
        self.receive_score(who,amount)
    async def core_game(self):
        ...
    async def _run(self):
        for i in range(self.num_rounds):
            if not self.num_rounds == 1:
                await self.basic_send(f"## {self.round_word.capitalize()} {i+1} of {self.num_rounds}:")
            await self.core_game()
            await self.announce_score()
    def generate_participant_placements(self) -> Placement[Participant]:
        return score_to_placement(self.point_totals,self.participants,not self.reverse_points)


class Rounds_With_Points_Base(Rounds_With_Points_Framework[PlayerId,int]):
    def __init__(self,gi:Game_Interface):
        Rounds_With_Points_Framework.__init__(self,gi)
        if not Rounds_With_Points_Base in self.initialized_bases:
            self.initialized_bases.append(Rounds_With_Points_Base)
            self.configure(self.unkicked_players)
            self.part_str = lambda player: self.format_players([player])
    def generate_placements(self) -> PlayerPlacement:
        return self.generate_participant_placements()
    async def score(self,who:Optional[PlayerId|Iterable[PlayerId]] = None,
            amount:Optional[int|Mapping[PlayerId,int]] = None,
            mute:bool = False):
        if not mute:
            await self.announce_score(who,amount)
        self.receive_score(who,amount)