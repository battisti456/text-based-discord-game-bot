from typing import override, Optional, Iterator
from dataclasses import dataclass

import chess
import json

from game import get_logger
from game.components.game_interface import Game_Interface
from game.components.player_input import Player_Text_Input, run_inputs, OnUpdate
from game.components.message import Message, Alias_Message
from game.game_bases.chess_base import chess_move_validator_maker
from game.game_bases import Chess_Base, Team_Base
from utils.types import Team, PlayerDict, PlayerId, Grouping, TeamDict
from utils.chess_tools import get_square_and_piece, get_move
from utils.pillow_tools import Color


logger = get_logger(__name__)

CHESS_PIECE_SHARING_PATH = 'data/chess_piece_sharing.json'
YOUR_PIECES_HIGHLIGHT:Color = '#4ea8f255'
MOVE_TO_HIGHLIGHT:Color = '#599f4355'

class Chess_War(Team_Base, Chess_Base):
    def __init__(self,gi:Game_Interface):
        Chess_Base.__init__(self,gi)
        Team_Base.__init__(self,gi)
        self.num_teams = 2
        self.num_rounds = None
        self.player_pieces:PlayerDict[set[chess.Square]]
        self.to_squares:TeamDict[To_Squares]
        self.last_to_squares:TeamDict[set[chess.Square]]
        self.team_board:TeamDict[Message]
        self.current_inputs:dict[Player_Text_Input,tuple[PlayerId,Team,chess.Square]]
        self.validate_boards:dict[Team,chess.Board] = {}
        with open(CHESS_PIECE_SHARING_PATH,'r') as file:
            self.chess_piece_sharing_data:dict[str,dict[str,list[list[chess.Square]]]] = json.load(file)
            "str(bool)/str(int)/list[list[square]]"
    @override
    async def game_intro(self):
        await self.basic_send(
            "# Welcome to a game of Chess War!\n" 
        )
    def get_color(self,team:Team) -> bool:
        return chess.WHITE if self.all_teams.index(team) == 0 else chess.BLACK
    @override
    async def game_setup(self):
        await super().game_setup()
        self.player_pieces = {}
        for team in self.all_teams:
            color = self.get_color(team)
            split = self.chess_piece_sharing_data[str(color).lower()][str(len(self.team_players[team]))]
            for i, player in enumerate(self.team_players[team]):
                self.player_pieces[player] = set(split[i])
        self.to_squares = {team:To_Squares(self,team) for team in self.all_teams}
    @override
    async def start_round(self):
        await super().start_round()
        self.current_inputs = {}
        self.team_board = {}
        self.last_to_squares = {team:set() for team in self.all_teams}
        for team in self.all_teams:
            self.team_board[team] = Alias_Message(
                Message("Your teams board:",channel_id=self.team_channeld[team]),
                attach_paths_modifier=lambda _: [self.make_board_image({
                    'white_perspective' : self.get_color(team),
                    'other_highlights' : {
                        square:MOVE_TO_HIGHLIGHT for square in self.to_squares[team]
                    }
                })]
            )
            await self.sender(self.team_board[team])
            board = self.board.copy()
            board.turn = self.get_color(team)
            self.validate_boards[team] = board
    def on_update_maker(self,inpt:Player_Text_Input) -> OnUpdate:
        player,team,square =  self.current_inputs[inpt]
        async def on_update():
            move = self.move_from_input(inpt)
            if move is None:
                return
            square_to = move.to_square
            #update other players inputs with the new informations, if needed
            for input_i,(player_i,team_i,square_i) in self.current_inputs.items():
                move_i = self.move_from_input(input_i)
                if move_i is None:
                    continue
                square_i_to = move_i.to_square
                if square_to == square_i_to and square != square_i:
                    await input_i.update_response_status()
            #change board image if something has changed
            current_team_squares = set(self.to_squares[team])
            if not self.last_to_squares[team] == set():
                if current_team_squares != self.last_to_squares[team]:
                    await self.sender(self.team_board[team])
            self.last_to_squares[team] = current_team_squares
        return on_update
    def move_from_input(self,inpt:Player_Text_Input) -> Optional[chess.Move]:
        player, team, square = self.current_inputs[inpt]
        if player not in inpt.responses:
            logger.error(f"player missing from their own input: input = {inpt}, player = {player}")
            return None
        text:str|None = inpt.responses[player]
        if text is None:
            return None
        move = get_move(text,square)
        return move
    @override
    async def core_player(self, team:Team, player: PlayerId):
        board_message:Message = Message(
            content="Here is your board:",
            attach_paths=[
                self.make_board_image({
                    'white_perspective' : self.get_color(team),
                    'other_highlights' : {
                        square:YOUR_PIECES_HIGHLIGHT for square in self.player_pieces[player]
                    }
                })
            ],
            players_who_can_see=[player]
        )
        await self.sender(board_message)
        pieces:dict[chess.Square,chess.Piece] = {}
        for square in self.player_pieces[player]:
            piece = self.board.piece_at(square)
            assert piece is not None
            pieces[square] = piece
        inputs:list[Player_Text_Input] = []
        for square, piece in pieces.items():
            message = Message(
                content=f"Where would you like to move {get_square_and_piece(square,piece)}?",
                players_who_can_see=[player]
            )
            inpt = Player_Text_Input(
                get_square_and_piece(square,piece),
                self.gi,
                self.sender,
                [player],
                chess_move_validator_maker(
                    from_squares=[square],
                    is_legal_on_any=[self.validate_boards[team]],
                    not_to_squares=self.to_squares[team]
                    ),
                who_can_see=[player],message=message
            )
            self.current_inputs[inpt] = (player,team,square)
            inpt.on_update(self.on_update_maker(inpt))
            inputs.append(inpt)
        await run_inputs(inputs)
    @override
    async def end_round(self):
        players_to_kick:set[PlayerId] = set()
        feedback:dict[chess.Square,set[str]] = {}
        eliminated:set[chess.Square] = set()

        #add all to_squares into eliminated
        for team in self.unkicked_teams:
            for from_square in self.to_squares[team]:
                from_piece = self.board.piece_at(from_square)
                assert from_piece is not None
                for to_square in chess.SQUARES:
                    to_piece = self.board.piece_at(to_square)
                    if to_piece is None:
                        continue
                    if to_square not in feedback:
                        feedback[to_square] = set()
                    feedback[to_square].add(f"Your piece {get_square_and_piece(to_square,to_piece)} was captured by {get_square_and_piece(from_square,from_piece)}.")
                    eliminated.add(to_square)
        #add eliminated pieces from pieces that moved to the same square
        for inpt,(player,team,square) in self.current_inputs.items():
            move = self.move_from_input(inpt)
            if move is None:
                players_to_kick.add(player)
                continue
            if move.to_square in eliminated:
                eliminated.add(square)
                if to_square not in feedback:
                    feedback[to_square] = set()
                piece = self.board.piece_at(square)
                assert piece is not None
                feedback[square].add(f"Your piece {get_square_and_piece(square,piece)} attempted to move to the same square as another piece")
                eliminated.add(square)
        #remove all eliminated pieces
        for player in self.unkicked_players:
            self.player_pieces[player] -= eliminated
        #move pieces
        for inpt,(player,team,square) in self.current_inputs.items():
            if square in self.player_pieces[player]:#not eliminated
                move = self.move_from_input(inpt)
                assert move is not None
                self.player_pieces[player].remove(square)
                self.player_pieces[player].add(move.to_square)
                piece = self.board.remove_piece_at(square)
                assert piece is not None
                self.board.set_piece_at(move.to_square,piece)
        #delete all the pieces that were eliminated
        for square in eliminated:
            self.board.remove_piece_at(square)
        #tally all pieces that need to be redistributed
        give_away:TeamDict[set[chess.Square]] = {team:set() for team in self.unkicked_teams}
        for player in players_to_kick:
            team:Team
            for _team in self.unkicked_teams:
                if player in self.team_players[_team]:
                    team = _team
                    break
            give_away[team].update(self.player_pieces[player])
        #redistrube extra pieces from players who responded None
        for team in self.unkicked_teams:
            for square in give_away[team]:
                min_number = min(len(self.player_pieces[player]) for player in self.team_players[team])
                player:PlayerId
                for _player in self.team_players[team]:
                    if len(self.player_pieces[_player]) == min_number:
                        player = _player
                        break
                self.player_pieces[player].add(square)
        #add any player with zero pieces to the list to kick
        no_pieces_players = set(player for player in self.unkicked_players if len(self.player_pieces[player]) == 0)
        await self.kick_players(players_to_kick,'timeout')
        await self.kick_players(no_pieces_players,'eliminated')
        await super().end_round()

@dataclass(frozen=True)
class To_Squares(Grouping[chess.Square]):
    game:Chess_War
    team:Team
    @override
    def __iter__(self) -> Iterator[chess.Square]:
        for inpt,(player,team,square) in self.game.current_inputs.items():
            if team == self.team:
                if player in inpt.responses:#should always be, methinks
                    move = self.game.move_from_input(inpt)
                    if move is not None:
                        yield move.to_square
    @override
    def __contains__(self,key:chess.Square, /) -> bool:
        return key in self.__iter__()
    @override
    def __len__(self) -> int:
        return len(list(self.__iter__()))