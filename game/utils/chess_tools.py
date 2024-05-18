from typing import Optional

import chess
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

from game.utils.pillow_tools import Color, Font

BOARD_SIZE = 8
FONT_START_SIZE = 1000

CASTLE_UCI_DICT = {
    'e1g1': "white castles kingside",
    'e8b8': "black castles queenside",
    'e1b1': "white castles queenside",
    'e8g8': "black castles kingside"
}
#region get text
def get_piece_name(piece:chess.Piece|str) -> str:
    if isinstance(piece,str):
        piece = chess.Piece.from_symbol(piece)
    return f"{chess.COLOR_NAMES[piece.color]} {chess.PIECE_NAMES[piece.piece_type]}"

def get_move_text(board:chess.Board,move_uci:chess.Move|str) -> str:
    if isinstance(move_uci,chess.Move):
        move_uci = move_uci.uci()
    def get_piece(uci:str) -> chess.Piece | None:
        piece = board.piece_at(eval(f"chess.{uci.upper()}"))
        return piece
    piece:chess.Piece | None = get_piece(move_uci[0:2])
    capture:chess.Piece | None = get_piece(move_uci[2:4])
    moves_to:str = 'moves to'
    and_text = ""
    check_text = ""

    assert piece is not None

    if (piece.piece_type == chess.PAWN and #en passant
        capture is None and #not capturing
        move_uci[0] != move_uci[2]):#but moving diagonally
        and_text = " en passant"
        capture_symbol = 'p'
        if piece.color == chess.BLACK:
            capture_symbol = 'P'
        capture = chess.Piece.from_symbol(capture_symbol)
    test = board.copy()
    test.push_uci(move_uci)
    if test.is_check():
        check_text = " resulting in a check"

    if capture is not None:#capturing
        moves_to = f'captures {get_piece_name(capture.symbol())} {capture.unicode_symbol()} on'

    if (piece.piece_type == chess.PAWN and len(move_uci) == 5):#promotion
        promote = chess.Piece.from_symbol(move_uci[4])
        and_text = f" and promotes into a {get_piece_name(move_uci[4])} {promote.unicode_symbol()}"
    elif piece.piece_type == chess.KING and move_uci in CASTLE_UCI_DICT:
            return f"{move_uci} - *{CASTLE_UCI_DICT[move_uci]}*"

    return f"{move_uci} - {get_piece_name(piece.symbol())} {piece.unicode_symbol()} on {move_uci[0:2]} {moves_to} {move_uci[2:4]}{and_text}{check_text}"

def get_game_over_text(board:chess.Board) -> str:
    #ending the game in ___
    if board.is_checkmate():
        return "checkmate"
    elif board.is_stalemate():
        return "stalemate"
    elif board.is_fifty_moves():
        return "a draw, since 100 moves have taken place without a pawn move or a capture, and a draw was claimed"
    elif board.is_seventyfive_moves():
        return "a draw, since 150 moves have taken place without a pawn move or a capture"
    elif board.is_insufficient_material():
        return "a draw due to insufficient material for either side to checkmate"
    return ""
#endregion
def render_chess(
        board:chess.Board,
        p_white_color:Color = 'seashell',
        p_black_color:Color = '#9e9e97',
        p_white_hollow:bool = False,
        p_black_hollow:bool = False,
        b_white_color:Color = 'beige',
        b_black_color:Color = '#478548',
        image_size:int = 1000,
        border_width:int = 75,
        back_grnd_color:Color = 'darkslategrey',
        text_color:Color = 'lightgrey',
        p_size:float = 1,
        p_font:Optional[str] = None,
        t_size:float = 0.75,
        t_font:Optional[str] = None,
        white_perspective:bool = True,
        p_white_outline:int = 2,
        p_black_outline:int = 2,
        p_white_outline_color:Color = 'black',
        p_black_outline_color:Color = 'black',
        last_move_color:Optional[Color] = '#eedc00d0',
        check_color:Optional[Color] = '#ff000066'
        ) -> PIL.Image.Image:
    """
    creates an image of the current state of a chess.Board as a PIL Image
    
    board: chess.Board object to draw piece position data from
    
    p_white_color: color of the white pieces
    
    p_black_color: color of the black pieces
    
    p_white_hollow: True to use unicode white piece chars for white pieces, False to use black

    p_black_hollow: True to use unicode white piece chars for black pieces, False to use black
    
    b_white_color: color for white spaces on board

    b_black_color: color for black spaces on board

    image_size: final image size in pixels (image will be a square)

    border_width: width in pixels of border around chessboard in the image

    back_grnd_color: color of the background behind the board, on which labels are printed

    text_color: color for rank and file labels

    p_size: float representing the fraction of the square the largest piece can take up

    p_font: path to font to use for drawing pieces

    t_size: fraction of the border to be taken up by the rank and file labels

    white_perspective: True to render the board from white's perspective, False for black's

    p_white_outline: width of outline to draw around white pieces

    p_black_outline: width of outline to draw around black pieces

    p_white_outline_color: color of the outline around white pieces

    p_black_outline_color: color of the outline around black pieces

    last_move_color: color to cover over the squares of the last move (from and to)

    check_color: color to color over the king's square when he is in check
    """
    #text spacing is still wierd
    square_edge = int((image_size - border_width*2)/BOARD_SIZE)
    square_size = (square_edge,square_edge)
    board_size = square_edge*BOARD_SIZE
    #region place squares
    board_image = PIL.Image.new('RGBA',(board_size,board_size),b_white_color)
    black_square = PIL.Image.new('RGBA',square_size,b_black_color)
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if (i%2 != j%2):
                board_image.paste(black_square,(i*square_edge,j*square_edge))
    #endregion
    #region special squares
    def square_to_xy(square:chess.Square) -> tuple[int,int]:
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        i = file if white_perspective else BOARD_SIZE - 1 - file
        j = BOARD_SIZE -1 - rank if white_perspective else rank
        return (i*square_edge,j*square_edge)

    if last_move_color is not None and len(board.move_stack)  > 0:
        last_move_square = PIL.Image.new('RGBA',square_size,last_move_color)
        last_move = board.peek()
        for square in (last_move.from_square,last_move.to_square):
            board_image.paste(
                last_move_square,
                square_to_xy(square),
                last_move_square
            )
    if check_color is not None and board.is_check():
        king_square = board.king(board.turn)
        if king_square is not None:
            check_square = PIL.Image.new('RGBA',square_size,check_color)
            board_image.paste(
                check_square,
                square_to_xy(king_square),
                check_square
            )
    #endregion
    #region place pieces
    draw = PIL.ImageDraw.ImageDraw(board_image,'RGBA')
    def get_font(size:float,path:Optional[str] = None) -> Font:
        if path is None:
            return PIL.ImageFont.load_default(size)
        else:
            return PIL.ImageFont.truetype(font=p_font,size=int(size))
    test_font = get_font(FONT_START_SIZE,p_font)
    max_size:int = 0
    for key in chess.UNICODE_PIECE_SYMBOLS:
        unicode:str = chess.UNICODE_PIECE_SYMBOLS[key]
        left,top,right,bottom = draw.textbbox((0,0),unicode,test_font)
        size = max(right-left,bottom-top)
        if size > max_size:
            max_size = size
    font = get_font(FONT_START_SIZE/max_size*(p_size*square_edge),p_font)
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            square:chess.Square
            if not white_perspective:
                square = chess.square(BOARD_SIZE-i-1,j)
            else:
                square = chess.square(i,BOARD_SIZE-j-1)
            val:chess.Piece|None = board.piece_at(square)
            if val is None:
                continue
            invert_unicode:bool
            if val.color == chess.WHITE:
                invert_unicode = not p_white_hollow
            else:
                invert_unicode = p_black_hollow
            unicode:str = val.unicode_symbol(invert_color=invert_unicode)
            draw.text(
                (
                    (i+0.5)*square_edge,
                    (j+0.5)*square_edge
                ),
                text=unicode,
                font = font,
                anchor='mm',
                fill=p_white_color if val.color else p_black_color,
                stroke_width=p_white_outline if val.color else p_black_outline,
                stroke_fill=p_white_outline_color if val.color else p_black_outline_color
            )
    #endregion
    final = PIL.Image.new('RGBA',(image_size,image_size),back_grnd_color)
    #region place markers
    draw = PIL.ImageDraw.ImageDraw(final)
    text_font = get_font(FONT_START_SIZE,t_font)
    left,top,right,bottom = draw.textbbox(
        (0,0),
        "".join(chess.FILE_NAMES) + "".join(chess.RANK_NAMES),
        text_font,
        'ls'
    )
    test_height = bottom - top
    text_size = int(FONT_START_SIZE/test_height*border_width*t_size)
    #vert_offset = int((bottom-top)/2/FONT_START_SIZE*text_size)
    vert_offset = 0
    text_font = get_font(text_size,t_font)
    ud_text_font = PIL.ImageFont.TransposedFont(text_font,PIL.Image.Transpose.ROTATE_180)
    for i in range(BOARD_SIZE):
        for j in range(4):
            vert = j%2 == 0
            other_side = j>1
            flip = other_side != vert#if we were going to go through the effort of flipping labels
            xy = (
                border_width+int((i+0.5) * square_edge),
                int(border_width/2) if not other_side else image_size - int(border_width/2)
            )
            if vert:
                xy = (xy[1],xy[0])
            xy = (xy[0]-(0 if flip else text_size/4),xy[1]+(vert_offset if flip else -vert_offset-text_size/4))
            index = BOARD_SIZE - i -1 if not white_perspective else i
            text = chess.RANK_NAMES[BOARD_SIZE - index - 1] if vert else chess.FILE_NAMES[index]
            draw.text(#horizontal labels
                xy,
                text,
                text_color,
                text_font if flip else ud_text_font,
                'mm'
            )
    #endregion
    final.paste(board_image,(border_width,border_width),board_image)
    return final