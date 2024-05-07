from typing import Optional

import chess
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

BOARD_SIZE = 8
FONT_START_SIZE = 1000
def render_chess(
        board:chess.Board,
        p_white_color:tuple[int,int,int],
        p_black_color:tuple[int,int,int],
        p_white_hollow:bool,
        p_black_hollow:bool,
        b_white_color:tuple[int,int,int],
        b_black_color:tuple[int,int,int],
        image_size:int,
        border_width:int,
        back_grnd_color:tuple[int,int,int],
        text_color:tuple[int,int,int],
        p_size:float = 1,
        p_font:Optional[str] = None,
        white_perspective:bool = True
        ) -> PIL.Image.Image:
    square_size = int((image_size - border_width*2)/BOARD_SIZE)
    board_size = square_size*BOARD_SIZE
    board_image = PIL.Image.new('RGB',(board_size,board_size),b_white_color)
    black_square = PIL.Image.new('RGB',(square_size,square_size),b_black_color)
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if (i%2 == j%2) == (not white_perspective):
                board_image.paste(black_square,(i*square_size,j*square_size))
    draw = PIL.ImageDraw.ImageDraw(board_image,'RGBA')
    def get_font(size:int) -> PIL.ImageFont.ImageFont|PIL.ImageFont.FreeTypeFont:
        if p_font is None:
            return PIL.ImageFont.load_default(size)
        else:
            return PIL.ImageFont.truetype(font=p_font,size=size)
    test_font = get_font(FONT_START_SIZE)
    max_size:int = 0
    for key in chess.UNICODE_PIECE_SYMBOLS:
        unicode:str = chess.UNICODE_PIECE_SYMBOLS[key]
        left,top,right,bottom = draw.textbbox((0,0),unicode,test_font)
        size = max(right-left,bottom-top)
        if size > max_size:
            max_size = size
    font = get_font(int(FONT_START_SIZE/max_size*(p_size*square_size)))
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            square:chess.Square
            if white_perspective:
                square = chess.square(i,j)
            else:
                square = chess.square(BOARD_SIZE-i-1,BOARD_SIZE-j-1)
            val:chess.Piece|None = board.piece_at(square)
            if val is None:
                continue
            invert_unicode:bool
            if val.color == chess.WHITE:
                invert_unicode = not p_white_hollow
            else:
                invert_unicode = p_black_hollow
            unicode:str = val.unicode_symbol(invert_color=invert_unicode)
            left,top,right,bottom = draw.textbbox((0,0),unicode,font)
            offset = (-int((left+right)/2),-int((top+bottom)/2))
            draw.text(
                (
                    int((i+0.5)*square_size + offset[0]),
                    int((j+0.5)*square_size+offset[1])
                ),
                text=unicode,
                font = font,
                fill=p_white_color if val.color else p_black_color
            )

    return board_image
    
if __name__ == '__main__':
    board = chess.Board()
    image = render_chess(
        board,
        (0,0,0),
        (255,255,255),
        True,
        False,
        (235, 236, 208),
        (119, 149, 86),
        1000,
        100,
        (0,0,0),
        (255,255,255),
        p_font = 'data/fonts/chess_merida_unicode.ttf',
        white_perspective=False
    )
    image.show()
    input()