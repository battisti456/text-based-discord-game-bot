import json
from typing import Callable, override, overload, Optional, Iterator
import dataclasses

import chess

from game import get_logger
from game.components.game_interface import Game_Interface
from game.components.message import Alias_Message, Bullet_Point, Message
from game.components.player_input import (
    Player_Single_Selection_Input,
    run_inputs,
    Player_Multi_Text_Input
)
from game.game_bases import Chess_Base, Team_Base
from utils.common import get_first
from utils.chess_tools import RenderChessOptional, get_move, get_move_text, capture_text
from utils.emoji_groups import NO_YES_EMOJI
from utils.pillow_tools import Color, get_color_name
from utils.types import PlayerDict, PlayerId, Team, TeamDict

logger = get_logger(__name__)

CHESS_PIECE_SHARING_PATH = 'data/chess_piece_sharing.json'
YOUR_PIECES_COLORS:Color = '#11a88d'

class Chess_War(Team_Base,Chess_Base):
    def __init__(self,gi:Game_Interface):
        Team_Base.__init__(self,gi)
        Chess_Base.__init__(self,gi)
        self.num_teams = 2
        self.num_rounds = None
        self.player_owned_squares:PlayerDict[set[chess.Square]]
        self.team_boards:TeamDict[chess.Board]
        self.team_board_messages:TeamDict[Message]
        with open(CHESS_PIECE_SHARING_PATH,'r') as file:
            self.chess_piece_sharing_data:dict[str,dict[str,list[list[chess.Square]]]] = json.load(file)
            "str(bool)/str(int)/list[list[square]]"
        self.team_moves:TeamDict[Move_Library]
        self.player_is_ready:PlayerDict[bool]
        self.all_ready:bool
    @override
    async def game_intro(self):
        ...#ADD GAME INTRO--------------------------------
    @override
    async def game_setup(self):
        await super().game_setup()
        self.player_owned_squares = {}
        self.team_board_messages = {}
        for team in self.all_teams:
            color = self.get_color(team)
            split = self.chess_piece_sharing_data[str(color).lower()][str(len(self.team_players[team]))]
            for i, player in enumerate(self.team_players[team]):
                self.player_owned_squares[player] = set(split[i])
            self.team_board_messages[team] = Alias_Message(
                Message(
                    content="Your team's board:",
                    channel_id=self.team_channel_id[team]
                ),
                attach_paths_modifier=self.make_team_board_callable(team)
            )

            
    @override
    async def start_round(self):
        await super().start_round()
        self.team_boards = {}
        self.team_moves = {}
        self.player_is_ready = {}
        self.all_ready = False
        for team in self.unkicked_teams:
            board = self.board.copy()
            board.turn = self.get_color(team)
            self.team_boards[team] = board
            self.team_moves[team] = Move_Library()
            for player in self.team_players[team]:
                self.player_is_ready[player] = False
            await self.show_team_board(team)
    @override
    async def core_player(self, team: Team, player: PlayerId):
        await super().core_player(team, player)
        def attatch_modifier(_:list[str]|None) -> list[str]|None:
            player_squares:set[chess.Square] = self.player_owned_squares[player].copy()
            for move in self.team_moves[team]:
                if move.from_square in player_squares:
                    player_squares.remove(move.from_square)
                    player_squares.add(move.to_square)
            return [self.make_team_board(team,{
                'other_colors' : {square:YOUR_PIECES_COLORS for square in player_squares}
            })]
        start_squares:set[chess.Square] = self.player_owned_squares[player]
        your_pieces_message:Message = Alias_Message(Message(
            content=f"Here is your board. The pieces you can move are colored {get_color_name(YOUR_PIECES_COLORS)}:",
            attach_paths=[
                self.make_board_image(
                    {
                        'white_perspective' : self.get_color(team),
                        'other_highlights' : {square:YOUR_PIECES_COLORS for square in start_squares}
                    }
                )
            ],
            players_who_can_see=[player]),
            attach_paths_modifier=attatch_modifier)
        await self.sender(your_pieces_message)
        @overload
        def validator(_,values:set[str]|None, return_legal_moves:None = ...) -> tuple[bool,str|None]:
            ...
        @overload
        def validator(_,values:set[str]|None, return_legal_moves:bool = ...) -> set[chess.Move]:
            ...
        def validator(_,values:set[str]|None, return_legal_moves:Optional[bool] = None) -> tuple[bool,str|None]|set[chess.Move]:
            if values is None:#not yet initialized
                return (True,None)
            moves = {text:get_move(text) for text in values}
            feedback:dict[str,str] = {}
            for text,move in moves.items():
                if move is None:
                    feedback[text] = f"'{text}' could not be interpreted"
                    continue
                self.board.turn = self.get_color(team)#set turn for is_legal check
                if not self.board.is_pseudo_legal(move):#is legal letting King get in check
                    feedback[text] = f"'{text}:{get_move_text(self.board,move)}' is not pseudo-legal in this position."
                    continue
                if self.board.is_castling(move):
                    feedback[text] = f"'{text}:{get_move_text(self.board,move)}' is not allowed because castling is not permitted in this game."
                    continue
                if self.board.is_en_passant(move):
                    feedback[text] = f"'{text}:{get_move_text(self.board,move)}' is not allowed because en passant is not permitted in this game."
                    continue
                if move.to_square in self.team_moves[team].to_squares():#make sure your team isn't already moving there
                    if move in self.team_moves[team]:
                        continue
                    other_from_square = self.team_moves[team].get_move_to(move.to_square)
                    player = get_first(player for player,owned in self.player_owned_squares.items() if other_from_square in owned)
                    feedback[text] = f"'{text}:{get_move_text(self.board,move)}' is not allowed because another piece from your team has already been moved to this position by {self.sender.format_players([player])}."
                    continue
                if move.to_square in list(square for player,square in self.player_owned_squares.items() if player in self.team_players[team]):
                    feedback[text] = f"'{text}:{get_move_text(self.board,move)}' is not allowed because your team started this turn with a piece on the destination square."
                    continue
            if return_legal_moves:
                return set(move for text,move in moves.items() if text not in feedback and move is not None)
            if feedback:
                return (False,'\n'.join(feedback.values()))
            else:
                return (True,None)

        move_input = Player_Multi_Text_Input(
            f"{self.sender.format_players([player])}'s moves input",
            self.gi,
            self.sender,
            [player],
            validator,
            [player],
            message=Message(
                content="What moves would you like your pieces to perform? Please enter moves in uci notation.",
                players_who_can_see=[player]
            )
        )
        @move_input.on_update
        async def on_update():
            response = move_input.responses[player]
            if response is None:
                return
            valid_moves = validator(player,response,True)
            undo_moves = self.team_moves[team] - valid_moves
            undo_moves = set(move for move in undo_moves if move.from_square in self.player_owned_squares[player])
            do_moves = valid_moves - self.team_moves[team]
            if not undo_moves and not do_moves:
                return
            for move in undo_moves:
                self.revert_team_board(team,move.from_square)
                self.revert_team_board(team,move.to_square)
                self.team_moves[team].remove(move)
            for move in do_moves:
                self.set_team_board(team,move)
                self.team_moves[team].add(move)
            await self.show_team_board(team)
            await self.sender(your_pieces_message)
        are_done = Player_Single_Selection_Input(
            name = f"{self.sender.format_players([player])}'s is ready input",
            gi = self.gi,
            sender = self.sender,
            players= [player],
            who_can_see=[player],
            message=Message(
                content="Are you ready to continue?",
                players_who_can_see=[player],
                bullet_points=[
                    Bullet_Point(
                        "yes",
                        NO_YES_EMOJI[1]
                    )
                ]
            )
        )
        await run_inputs(
            inputs = (move_input,are_done),
            sender = self.sender,
            basic_feedback=True,
            id=player,
            sync_call=self.sync_call
        )
    @override
    async def end_round(self):
        #attacks
        feedback_text:TeamDict[set[str]] = {team:set() for team in self.all_teams}
        for team in self.all_teams:
            other_team = get_first(other_team for other_team in self.all_teams if other_team != team)
            for move in self.team_moves[other_team]:
                piece = self.team_boards[team].remove_piece_at(move.to_square)
                if piece is None:
                    continue
                killer = self.board.remove_piece_at(move.from_square)
                assert killer is not None
                feedback_text[team].add(
                    capture_text(move.from_square,killer,move.to_square,piece)
                )
        #merge
        team1,team2 = self.all_teams
        for square in chess.SQUARES:
            piece1 = self.team_boards[team1].piece_at(square)
            piece2 = self.team_boards[team2].piece_at(square)
            if piece1 is not None:
                if piece1.color != self.get_color(team1):
                    piece1 = None
            if piece2 is not None:
                if piece2.color != self.get_color(team2):
                    piece2 = None
            player1,from1 = self.get_player(team1,square)
            player2,from2 = self.get_player(team2,square)
            if piece1 is not None and piece2 is not None and piece1 != piece2:
                #collision
                text = collision_text(piece1,piece2,square)
                for team in self.all_teams:
                    feedback_text[team].add(text)
                self.board.set_piece_at(
                    square,
                    None
                )
                if player1 is not None:
                    assert from1 is not None
                    self.player_owned_squares[player1].remove(from1)
                if player2 is not None:
                    assert from2 is not None
                    self.player_owned_squares[player2].remove(from2)
            else:
                self.board.set_piece_at(
                    square,
                    piece1 if piece1 is not None else piece2
                    )
                if player1 is not None:
                    assert from1 is not None
                    self.player_owned_squares[player1].remove(from1)
                    self.player_owned_squares[player1].add(square)
                elif player2 is not None:
                    assert from2 is not None
                    self.player_owned_squares[player2].remove(from2)
                    self.player_owned_squares[player2].add(square)
        for team in self.all_teams:
            await self.basic_send(
                content = '\n'.join(feedback_text[team]),
                channel_id = self.team_channel_id[team]
            )
            await self.show_team_board(team)
        #ADD PLAYER KICKING LOGIC --------------------------------------use self.player_is_ready
        #ADD END-GAME LOGIC---------------------------------------------------------------------------
        await super().end_round()
    def get_color(self,team:Team) -> chess.Color:
        return chess.WHITE if self.all_teams.index(team) == 0 else chess.BLACK
    def revert_team_board(self,team:Team,square:chess.Square):
        self.team_boards[team].set_piece_at(
            square = square,
            piece = self.board.piece_at(square)
        )
    def set_team_board(self,team:Team,move:chess.Move):
        piece = self.team_boards[team].piece_at(move.from_square)
        if piece is not None and move.promotion is not None:
            piece.piece_type = move.promotion
        self.team_boards[team].set_piece_at(move.from_square,None)
        self.team_boards[team].set_piece_at(move.to_square,piece)
    async def show_team_board(self,team:Team):
        await self.sender(self.team_board_messages[team])
    def make_team_board(self,team:Team,extra_args:RenderChessOptional = {}) -> str:
        board = self.team_boards[team]
        args:RenderChessOptional = {#type: ignore
            'board' : board,
            'white_perspective' : self.get_color(team)
        }|extra_args
        return self.make_board_image(args)
    def make_team_board_callable(self,team:Team,extra_args:RenderChessOptional = {}) -> Callable[[list[str]|None],list[str]|None]:
        def wrapper(_:list[str]|None) -> list[str]|None:
            return [self.make_team_board(team,extra_args)]
        return wrapper
    def sync_call(self,id:PlayerId,completed:bool) -> bool:
        self.player_is_ready[id] = completed
        if self.all_ready:
            return True
        all_ready = all(complete for complete in self.player_is_ready.values())
        if all_ready:
            self.all_ready = True
            return True
        return False
    def get_player(self,team:Team,to_square:chess.Square) -> tuple[PlayerId|None, chess.Square|None]:
        try:
            move = self.team_moves[team].get_move_to(to_square)
        except IndexError:
            return None,None
        return get_first(
            player for player in self.team_players[team]
            if move.from_square in self.player_owned_squares[player]), move.from_square

@dataclasses.dataclass
class Move_Library(set[chess.Move]):
    def from_squares(self) -> Iterator[chess.Square]:
        return (move.from_square for move in self)
    def to_squares(self) -> Iterator[chess.Square]:
        return (move.to_square for move in self)
    def get_move_from(self,from_square:chess.Square) -> chess.Move:
        return get_first(move for move in self if move.from_square == from_square)
    def get_move_to(self,to_square:chess.Square) -> chess.Move:
        return get_first(move for move in self if move.to_square == to_square)
    
def collision_text(piece1:chess.Piece,piece2:chess.Piece,square:chess.Square) -> str:
    return ""