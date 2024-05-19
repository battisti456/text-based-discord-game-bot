from typing import Optional, Sequence

import chess

from config.game_bases_config import game_bases_config
from game.components.game_interface import Game_Interface
from game.components.response_validator import ResponseValidator, Validation
from game.game import Game
from game.utils.chess_tools import get_move, get_square_name, render_chess
from game.utils.common import get_first
from game.utils.grammer import temp_file_path, wordify_iterable
from game.utils.pillow_tools import Color
from game.utils.types import Grouping, PlayerId

CONFIG = game_bases_config['chess_base']

def chess_move_validator_maker(
        from_squares:Optional[Grouping[chess.Square]] = None,
        to_squares:Optional[Grouping[chess.Square]] = None,
        not_from_squares:Optional[Grouping[chess.Square]] = None,
        not_to_squares:Optional[Grouping[chess.Square]] = None,
        move_in:Optional[Sequence[chess.Move]] = None,
        move_not_in:Optional[Sequence[chess.Move]] = None,
        is_legal_on_any:Optional[Sequence[chess.Board]] = None) -> ResponseValidator[str]:
    def validator(player:PlayerId,content:str|None) -> Validation:
        if content is None:
            return (False,None)
        move:chess.Move|None = get_move(
            content,
            None if not from_squares else get_first(from_squares),
            None if not to_squares else get_first(to_squares))
        if move is None:
            return (
                False,
                f"given text '{content}' could not be interpreted into a move, please use the uci format where a1b2 is a move from a1 to b2")
        if from_squares is not None:
            if move.from_square not in from_squares:
                return (
                    False,
                    f"given move '{move.uci()}' starts from '{get_square_name(move.from_square)}', but needs to start from " + 
                    f"{wordify_iterable((get_square_name(square) for square in from_squares),operator='or')}")
        if to_squares is not None:
            if move.to_square not in to_squares:
                return (
                    False,
                    f"given move '{move.uci()}' ends at '{get_square_name(move.to_square)}', but needs to end at " + 
                    f"{wordify_iterable((get_square_name(square) for square in to_squares),operator='or')}")
        if not_from_squares is not None:
            if move.from_square not in not_from_squares:
                return (
                    False,
                    f"given move '{move.uci()}' starts from '{get_square_name(move.from_square)}', but needs to not start from " + 
                    f"{wordify_iterable((get_square_name(square) for square in not_from_squares),operator='or')}")
        if not_to_squares is not None:
            if move.to_square not in not_to_squares:
                return (
                    False,
                    f"given move '{move.uci()}' ends at '{get_square_name(move.to_square)}', but needs to not end at " + 
                    f"{wordify_iterable((get_square_name(square) for square in not_to_squares),operator='or')}")
        if move_in is not None:
            if move not in move_in:
                return (
                    False,
                    f"given move '{move.uci()}' not in the list of permitted moves"
                )
        if move_not_in is not None:
            if move in move_not_in:
                return (
                    False,
                    f"given move '{move.uci()}' is in the list of not permitted moves"
                )
        if is_legal_on_any is not None:
            if not any(board.is_legal(move) for board in is_legal_on_any):
                return (
                    False,
                    f"given move '{move.uci()}' is not a legal move"
                )
        return (True,None)
    return validator

class Chess_Base(Game):
    def __init__(self,gi:Game_Interface):
        super().__init__(gi)
        if Chess_Base not in self.initialized_bases:
            self.initialized_bases.append(Chess_Base)
            self.board = chess.Board()
            self.p_white_color:Color = CONFIG['p_white_color']
            self.p_black_color:Color = CONFIG['p_black_color']
            self.p_white_hollow:bool = CONFIG['p_white_hollow']
            self.p_black_hollow:bool = CONFIG['p_black_hollow']
            self.b_white_color:Color = CONFIG['b_white_color']
            self.b_black_color:Color = CONFIG['b_black_color']
            self.image_size:int = CONFIG['image_size']
            self.border_width:int = CONFIG['border_width']
            self.back_grnd_color:Color = CONFIG['back_grnd_color']
            self.text_color:Color = CONFIG['text_color']
            self.p_size:float = CONFIG['p_size']
            self.p_font:Optional[str] = CONFIG['p_font']
            self.t_size:float = CONFIG['t_size']
            self.t_font:Optional[str] = CONFIG['t_font']
            self.white_perspective:bool = CONFIG['white_perspective']
            self.p_white_outline:int = CONFIG['p_white_outline']
            self.p_black_outline:int = CONFIG['p_black_outline']
            self.p_white_outline_color:Color = CONFIG['p_white_outline_color']
            self.p_black_outline_color:Color = CONFIG['p_black_outline_color']
            self.last_move_color:Optional[Color] = CONFIG['last_move_color']
            self.check_color:Optional[Color] = CONFIG['check_color']
    def make_board_image(self) -> str:
        image = render_chess(
            self.board,
            self.p_white_color,
            self.p_black_color,
            self.p_white_hollow,
            self.p_black_hollow,
            self.b_white_color,
            self.b_black_color,
            self.image_size,
            self.border_width,
            self.back_grnd_color,
            self.text_color,
            self.p_size,
            self.p_font,
            self.t_size,
            self.t_font,
            self.white_perspective,
            self.p_white_outline,
            self.p_black_outline,
            self.p_white_outline_color,
            self.p_black_outline_color,
            self.last_move_color,
            self.check_color
        )
        file_path = temp_file_path('.png')
        image.save(file_path)
        return file_path