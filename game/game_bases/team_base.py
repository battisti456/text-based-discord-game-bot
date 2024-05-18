import asyncio
from typing import Optional

from game import kick_text
from game.components.game_interface import Game_Interface
from game.game import Game
from game.game_bases.rounds_with_points_base import Rounds_With_Points_Framework
from game.utils.common import arg_fix_grouping
from game.utils.exceptions import GameEndInsufficientTeams
from game.utils.grammer import wordify_iterable
from game.utils.types import (
    Grouping,
    KickReason,
    Placement,
    PlayerId,
    PlayerPlacement,
    Team,
    TeamDict,
)
from game.utils.word_tools import word_generator


def random_team_name() -> Team:
    adj:str = word_generator.word(include_categories=['adjective'])
    noun:str = word_generator.word(include_categories=['noun'])
    return Team(f"The {adj.capitalize()} {noun.capitalize()}s")

def team_to_player_placements(team_placement:Placement[Team],team_players:TeamDict[frozenset[PlayerId]]) -> PlayerPlacement:
    working_placement:list[tuple[PlayerId,...]] = []
    for team_group in team_placement:
        working_placement.append(tuple(set().union(*(team_players[team] for team in team_group))))
    return tuple(working_placement)
def format_team(teams:Grouping[Team]|Team) -> str:
    teams = arg_fix_grouping([],teams)
    return wordify_iterable(str(team) for team in teams)

class Team_Base(Game):
    """
    a base for working with your players in teams; 
    will split your players (as evenly as possible) into self.num_teams teams with random names, defualts to 2;
    it will run core_game;
    then it will run self.team_game for each team, either in sequence or concurrently if self.concurrent is True, defualts to True;
    generate placements would need to be defined in any inheriting games
    """
    def __init__(self,gi:Game_Interface):
        Game.__init__(self,gi)
        if Team_Base not in self.initialized_bases:
            self.initialized_bases.append(Team_Base)
            self.num_teams:int = 2
            self.concurrent:bool = True
            self.setup_teams()
            self.team_kicked:dict[Team,tuple[int,KickReason]] = {}
    def setup_teams(self):
        self.teams:tuple[Team,...] = tuple(random_team_name() for _ in range(self.num_teams))
        self.team_players:TeamDict[frozenset[PlayerId]] = {
            self.teams[i]:frozenset(self.unkicked_players[i::self.num_teams])
            for i in range(self.num_teams)
        }
    async def kick_teams(
            self,
            teams:Grouping[Team],
            reason:KickReason = 'unspecified',
            priority:Optional[int] = None) :
        """
        adds players to the kicked dict with the approprite priority and reason

        players: a list of players to eliminate
        reason: one of a set list of reasons which might have further implications elsewhere
        priority: where should these players be placed in the order of their elimination, if None, assumes after the lastmost eliminated of players so far
        """
        if priority is None:
            priority = self.max_kick_priority() + 1
        for team in teams:
            self.team_kicked[team] = (priority,reason)
        if len(self.unkicked_players) <= 1:
            raise GameEndInsufficientTeams(f"{format_team(teams)} being {kick_text[reason]}")
    async def _run(self):
        await self.core_game()
    async def core_team(self,team:Team):
        ...
    async def core_game(self):
        if not self.concurrent:
            for team in self.teams:
                await self.core_team(team)
        else:
            tasks:list[asyncio.Task] = list(asyncio.create_task(self.core_team(team)) for team in self.teams)
            asyncio.gather(*tasks)


class Rounds_With_Points_Team_Base(Rounds_With_Points_Framework[Team,int],Team_Base):
    def __init__(self,gi:Game_Interface):
        Rounds_With_Points_Framework.__init__(self,gi)#type:ignore
        Team_Base.__init__(self,gi)
        if Rounds_With_Points_Team_Base not in self.initialized_bases:
            self.initialized_bases.append(Rounds_With_Points_Team_Base)
    def generate_placements(self) -> PlayerPlacement:
        return team_to_player_placements(self.generate_participant_placements(),self.team_players)