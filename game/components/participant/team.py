from dataclasses import dataclass

from game.components.participant.participant import Participant


@dataclass(frozen=True)
class Team(Participant):
    ...