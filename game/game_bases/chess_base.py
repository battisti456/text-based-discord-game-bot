import chess
import PIL.Image

BOARD_SIZE = 8

def render_chess(
        board:chess.Board,
        pieces_dict:dict[chess.PieceType,PIL.Image.Image],
        p_white_color:tuple[int,int,int],
        p_black_color:tuple[int,int,int],
        b_white_color:tuple[int,int,int],
        b_black_color:tuple[int,int,int],
        image_size:int,
        border_width:int,
        back_grnd_color:tuple[int,int,int],
        text_color:tuple[int,int,int]
        ) -> PIL.Image.Image:
    square_size = int((image_size - border_width*2)/BOARD_SIZE)
    board_size = square_size*BOARD_SIZE
    board_image = PIL.Image.new('rgb',(board_size,board_size),b_white_color)
    black_square = PIL.Image.new('rgb',(square_size,square_size),b_black_color)
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if not i%2 == j%2:
                board_image.paste(black_square,(i*square_size,j*square_size))
    return board_image
    
