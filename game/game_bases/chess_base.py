from typing import Optional

import chess

from game.utils.pillow_tools import Color
from game.game import Game
from game.components.game_interface import Game_Interface
from game.utils.grammer import temp_file_path
from game.utils.chess_tools import render_chess

from config.game_bases_config import game_bases_config

CONFIG = game_bases_config['chess_base']

class Chess_Base(Game):
    def __init__(self,gi:Game_Interface):
        super().__init__(gi)
        if not Chess_Base in self.initialized_bases:
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