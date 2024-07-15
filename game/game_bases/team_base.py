import asyncio
from typing import Optional, override

from game import kick_text
from game.components.game_interface import Game_Interface
from game.components.send.old_message import Old_Message
from game.game_bases.elimination_base import Elimination_Framework
from game.game_bases.round_base import Rounds_Base
from game.game_bases.rounds_with_points_base import Rounds_With_Points_Framework
from utils.common import arg_fix_grouping
from utils.exceptions import GameEndInsufficientTeams
from utils.grammar import wordify_iterable
from utils.types import (
    ChannelId,
    Grouping,
    KickReason,  # noqa: F811
    Placement,
    PlayerId,
    PlayerPlacement,
    Team,
    TeamDict,
)
from utils.word_tools import word_generator


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

class Team_Base(Rounds_Base[Team]):
    """
    a base for working with your players in teams; 
    will split your players (as evenly as possible) into self.num_teams teams with random names, defaults to 2;
    it will run core_game;
    then it will run self.team_game for each team, either in sequence or concurrently if self.concurrent is True, defaults to True;
    generate placements would need to be defined in any inheriting games
    """
    def __init__(self,gi:Game_Interface):
        Rounds_Base.__init__(self,gi)#type:ignore
        if Team_Base not in self.initialized_bases:
            self.initialized_bases.append(Team_Base)
            self.num_teams:int = 2
            self.players_concurrent = True
            self.team_kicked:dict[Team,tuple[int,KickReason]] = {}
            self.all_teams:tuple[Team,...]
            self.num_rounds = 1
    def is_team_kicked(self,team:Team) -> bool:
        return team in self.team_kicked
    @property
    def kicked_teams(self) -> tuple[Team, ...]:
        return tuple(team for team in self.all_teams if self.is_team_kicked(team))
    @property
    def unkicked_teams(self) -> tuple[Team, ...]:
        return tuple(team for team in self.all_teams if not self.is_team_kicked(team))
    @override
    async def game_setup(self):
        await super().game_setup()
        self.all_teams:tuple[Team,...] = tuple(random_team_name() for _ in range(self.num_teams))
        self.team_players:TeamDict[frozenset[PlayerId]] = {
            self.all_teams[i]:frozenset(self.unkicked_players[i::self.num_teams])
            for i in range(self.num_teams)
        }
        self.team_channel_id:TeamDict[ChannelId] = {
            team:await self.gi.new_channel(
                f"{str(team)}'s Team Channel",
                self.team_players[team]
            ) for team in self.all_teams
        }
        for team in self.all_teams:
            await self.say(
                f"On team '{team}' we have {self.sender.format_players(self.team_players[team])}!"
            )
    async def basic_send_team(
            self,
            teams:Grouping[Team]|Team|None,
            content:Optional[str] = None,
            attachments_data:list[str] = []):
        """
        creates a message with the given parameters and sends it with self.sender

        teams: the teams to send the message to on their channels, if None defaults to all teams
        
        content: the text content of the message
        
        attachments_data: a list of file paths to attach to the message
        """
        teams = arg_fix_grouping(self.all_teams,teams)
        for team in teams:
            await self.sender(Old_Message(
                text=content,
                attach_files=attachments_data,
                on_channel=self.team_channel_id[team]
            ))
    async def kick_teams(
            self,
            teams:Grouping[Team],
            reason:KickReason = 'unspecified',
            priority:Optional[int] = None) :
        """
        adds teams to the team_kicked dict with the appropriate priority and reason

        teams: a list of teams to eliminate

        reason: one of a set list of reasons which might have further implications elsewhere

        priority: where should these teams be placed in the order of their elimination, if None, assumes after the last-most eliminated of teams so far
        """
        if priority is None:
            priority = self.max_kick_priority() + 1
        for team in teams:
            self.team_kicked[team] = (priority,reason)
        if len(self.unkicked_teams) <= 1:
            raise GameEndInsufficientTeams(f"{format_team(teams)} being {kick_text[reason]}")
    async def core_player(self,team:Team,player:PlayerId):
        ...
    @override
    async def participant_round(self,team:Team):
        if not self.players_concurrent:
            for player in self.team_players[team]:
                await self.core_player(team,player)
        else:
            tasks:list[asyncio.Task] = list(asyncio.create_task(self.core_player(team,player)) for player in self.team_players[team])
            await asyncio.gather(*tasks)
    @override
    async def kick_players(self, players: Grouping[PlayerId], reason:KickReason = 'unspecified', priority: Optional[int]= None):
        await super().kick_players(players, reason, priority)
        kick_teams = tuple(team for team in self.unkicked_teams if all(self.is_player_kicked(player) for player in self.team_players[team]))
        if kick_teams:
            await self.kick_teams(kick_teams,reason)
    def _generate_team_placements(self) -> Placement[Team]:
        ...
    @override
    def generate_placements(self) -> Placement[PlayerId]:
        return team_to_player_placements(
            self._generate_team_placements(),self.team_players
        )



class Rounds_With_Points_Team_Base(Team_Base,Rounds_With_Points_Framework[Team,int]):
    def __init__(self,gi:Game_Interface):
        Team_Base.__init__(self,gi)
        Rounds_With_Points_Framework.__init__(self,gi) # type: ignore
        if Rounds_With_Points_Team_Base not in self.initialized_bases:
            self.initialized_bases.append(Rounds_With_Points_Team_Base)
    @override
    def _configure_participants(self):
        self._participants = self.all_teams
    @override
    def _generate_team_placements(self) -> Placement[Team]:
        return self._generate_participant_placements()
    @override
    async def _run(self):
        await Rounds_With_Points_Framework._run(self) #type:ignore


class Elimination_Team_Base(Team_Base,Elimination_Framework[Team]):
    def __init__(self,gi:Game_Interface):
        Team_Base.__init__(self,gi)
        Elimination_Framework(self,gi)#type:ignore
        if Elimination_Team_Base not in self.initialized_bases:
            self.initialized_bases.append(Elimination_Framework)
    @override
    def _configure_participants(self):
        self._participants = self.all_teams
    @override
    async def _run(self):
        await Elimination_Framework._run(self)#type:ignore
