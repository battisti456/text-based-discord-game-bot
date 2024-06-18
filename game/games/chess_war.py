import json
from typing import Callable, override, overload, Optional, Iterator
import dataclasses

import chess

from game import get_logger
from game.components.send.option import Option
from game.components.game_interface import Game_Interface
from game.components.player_input import (
    Player_Single_Selection_Input,
    run_inputs,
)
from game.components.send.old_message import Old_Message, _Old_Message
from game.game_bases import Chess_Base, Team_Base
from utils.grammar import wordify_iterable
from utils.common import get_first
from utils.chess_tools import RenderChessOptional, get_move, get_move_text, capture_text, get_piece_name
from utils.emoji_groups import NO_YES_EMOJI
from utils.pillow_tools import Color, get_color_name
from utils.types import Placement, PlayerDict, PlayerId, Team, TeamDict

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
        self.team_board_messages:TeamDict[_Old_Message]
        with open(CHESS_PIECE_SHARING_PATH,'r') as file:
            self.chess_piece_sharing_data:dict[str,dict[str,list[list[chess.Square]]]] = json.load(file)
            "str(bool)/str(int)/list[list[square]]"
        self.team_moves:TeamDict[Move_Library]
        self.player_is_ready:PlayerDict[bool]
        self.all_ready:bool
        self.team_board_player_messages:TeamDict[set[_Old_Message]]
    @override
    async def game_intro(self):
        await self.basic_send(
            "# Welcome to a game of chess war!\n" + 
            "In this game we have two teams, one playing for white and the other playing for black.\n" +
            "Everyone is given a fair portion of their team's chess pieces and plays simultaneously\n" +
            "Except, unlike chess, the objective is just to capture all of the enemy teams pieces, kings have no more value than as a normal piece.\n" +
            "On your turn you can move each of the pieces you have control over, and press the check mark when you are done.\n" +
            "If you capture an opponent's piece, their piece is eliminated, but if your piece is captured on its starting square on their team board, your piece is also eliminated." +
            "If two pieces try to move to the same square they are both eliminated i a collision."
        )
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
                Old_Message(
                    text="Your team's board:",
                    on_channel=self.team_channel_id[team]
                ),
                attach_paths_modifier=self.make_team_board_callable(team)
            )
    @override
    async def start_round(self):
        await super().start_round()
        self.team_boards = {}
        self.team_moves = {}
        self.player_is_ready = {}
        self.team_board_player_messages = {}
        self.all_ready = False
        for team in self.unkicked_teams:
            board = self.board.copy()
            board.turn = self.get_color(team)
            self.team_boards[team] = board
            self.team_moves[team] = Move_Library()
            self.team_board_player_messages[team] = set()
            for player in self.team_players[team]:
                self.player_is_ready[player] = False
            await self.show_team_board(team)
    @override
    async def core_player(self, team: Team, player: PlayerId):
        await super().core_player(team, player)
        def attach_modifier(_:list[str]|None) -> list[str]|None:
            player_squares:set[chess.Square] = self.player_owned_squares[player].copy()
            for move in self.team_moves[team]:
                if move.from_square in player_squares:
                    player_squares.remove(move.from_square)
                    player_squares.add(move.to_square)
            return [self.make_team_board(team,{
                'other_colors' : {square:YOUR_PIECES_COLORS for square in player_squares}
            })]
        start_squares:set[chess.Square] = self.player_owned_squares[player]
        your_pieces_message:Old_Message = Alias_Message(Old_Message(
            text=f"Here is your board. The pieces you can move are colored {get_color_name(YOUR_PIECES_COLORS)}:",
            attach_files=[
                self.make_board_image(
                    {
                        'white_perspective' : self.get_color(team),
                        'other_highlights' : {square:YOUR_PIECES_COLORS for square in start_squares}
                    }
                )
            ],
            limit_players_who_can_see=[player]),
            attach_paths_modifier=attach_modifier)
        self.team_board_player_messages[team].add(your_pieces_message)
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
                if move.from_square not in self.player_owned_squares[player]:
                    feedback[text] = f"starting square '{chess.SQUARE_NAMES[move.from_square]}' is not owned by you"
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
                    other_player = get_first(player for player,owned in self.player_owned_squares.items() if other_from_square in owned)
                    feedback[text] = f"'{text}:{get_move_text(self.board,move)}' is not allowed because another piece from your team has already been moved to this position by {self.sender.format_players([other_player])}."
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
            message=Old_Message(
                text="What moves would you like your pieces to perform? Please enter moves in uci notation.",
                limit_players_who_can_see=[player]
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
            #await self.sender(your_pieces_message)
        are_done = Player_Single_Selection_Input(
            name = f"{self.sender.format_players([player])}'s is ready input",
            gi = self.gi,
            sender = self.sender,
            players= [player],
            who_can_see=[player],
            message=Old_Message(
                text="Are you ready to continue?",
                limit_players_who_can_see=[player],
                with_options=[
                    Option(
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
        #removed killed pieces from their team's boards
        feedback_text:PlayerDict[set[str]] = {player:set() for player in self.unkicked_players}
        for team in self.all_teams:
            other_team = get_first(other_team for other_team in self.all_teams if other_team != team)
            for move in self.team_moves[other_team]:
                piece = self.team_boards[team].remove_piece_at(move.to_square)
                player = get_first(
                    player for player in self.team_players[team] 
                    if move.to_square in self.player_owned_squares[player])
                if piece is None:
                    continue
                killer = self.board.remove_piece_at(move.from_square)
                assert killer is not None
                feedback_text[player].add(
                    capture_text(move.from_square,killer,move.to_square,piece)
                )
        #merge team boards into main board
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
                self.board.set_piece_at(
                    square,
                    None
                )
                if player1 is not None:
                    assert from1 is not None
                    feedback_text[player1].add(text)
                    self.player_owned_squares[player1].remove(from1)
                if player2 is not None:
                    assert from2 is not None
                    feedback_text[player2].add(text)
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
        for player in self.unkicked_players:
            if feedback_text[player]:
                await self.sender(Old_Message(
                    text=f"On this turn your pieces died from: {wordify_iterable(feedback_text[player])}",
                    limit_players_who_can_see=[player]
                ))
        for team in self.all_teams:
            await self.show_team_board(team)
        #ADD PLAYER KICKING LOGIC --------------------------------------use self.player_is_ready
        """for team in self.all_teams:
            players_to_kick = set(
                player for player in self.unkicked_players if 
                player in self.team_players[team] and #part of the current team
                not self.player_is_ready[player])#player did not answer they were ready, must have timed out
            free_squares = set().union(
                squares for player,squares in self.player_owned_squares.items() 
                if player in players_to_kick)
            for player in players_to_kick:
                del self.player_owned_squares[player]"""
            
        
        #ADD END-GAME LOGIC---------------------------------------------------------------------------
        team_owned_square:TeamDict[set[chess.Square]] = {}
        for team in self.all_teams:
            team_owned_square[team] = set().union(*(
                squares for player,squares in self.player_owned_squares.items() 
                if player in self.team_players[team]))
            if len(team_owned_square[team]) == 0:
                await self.kick_teams([team],'eliminated')#should trigger one team remaining end of game
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
        for message in self.team_board_player_messages[team]:
            await self.sender(message)
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
    @override
    def _generate_team_placements(self) -> Placement[Team]:
        team_owned_square:TeamDict[set[chess.Square]] = {}
        for team in self.all_teams:
            team_owned_square[team] = set().union(*(
                squares for player,squares in self.player_owned_squares.items() 
                if player in self.team_players[team]))
        teams = list(self.all_teams)
        teams.sort(key=lambda team: len(team_owned_square[team]),reverse=True)
        return tuple((team,) for team in teams)

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
    return f"a collision on  between {get_piece_name(piece1)} and {get_piece_name(piece2)}"