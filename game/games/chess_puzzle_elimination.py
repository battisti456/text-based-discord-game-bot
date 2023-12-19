import game
from game import userid
from typing import TypedDict

from game.game_bases import Elimination_Base
from random import randint

import chessboard.board
import chess
import pygame
import PIL.Image
import PIL.ImageDraw
import PIL.ImageOps
import PIL.ImageFont
import random



import pandas

DATA_PATH = "lichess_db_puzzle.csv"
ORIGINAL_BG_COLOR = (0,0,0)

RATING_RANGE = (400,800)
POPULARITY_RANGE = None
NUM_TO_SAMPLE = 500

NUM_MOVE_OPTIONS = 5

COLOR_NAMES = {
    chess.WHITE : 'white',
    chess.BLACK : 'black'
}

PIECE_NAMES = {
    'p' : 'pawn',
    'k' : 'king',
    'r' : 'rook',
    'b' : 'bishop',
    'q' : 'queen',
    'n' : 'knight'
}

CASTLE_UCI_DICT = {
    'e1g1': "white castles kingside",
    'e8b8': "black castles queenside",
    'e1b1': "white castles queenside",
    'e8g8': "black castles kingside"
}
PUZZLE_RATING_CAP_ESCALATION = 200
ORIGINAL_BOARD_SIZE = (600,600)
ORIGINAL_BOARDER_WIDTH = 100

SET_IMAGE_SIZE = (1500,1500)

TEXT_COLOR = (255,255,255)
NEW_BOARDER_WIDTH = 100
NEW_BOARDER_COLOR = (0,0,0)

COL_LABELS = "abcdefgh"
ROW_LABELS = "12345678"
NUM_TILES = 8
SIDE_LABEL_OFFSET = int(NEW_BOARDER_WIDTH/4)
BOTTOM_LABEL_OFFSET = SET_IMAGE_SIZE[1]+NEW_BOARDER_WIDTH
LABEL_FONT_SIZE = 65

def piece_name(symbol:str):
    color = 'white'
    if symbol.lower() == symbol:
        color = 'black'
    return f"{color} {PIECE_NAMES[symbol.lower()]}"

#PuzzleId,FEN,Moves,Rating,RatingDeviation,Popularity,NbPlays,Themes,GameUrl,OpeningTags
class ChessPuzzleDict(TypedDict):
    PuzzleId:str
    FEN:str#starting position (before first move)
    Moves:str#space separated ordered intended moves, first move by bot
    Rating:int#recommended chess rating
    RatingDeviation:int
    Popularity:int#lichess average popluarity out of 100
    NbPlays:int#number of plays in lichess
    Themes:str#space seperated theme tags
    GameUrl:str#lichess puzzle url
    OpeningTags:str#space seperated opening tags

class Chess_Puzzle_Elimination(Elimination_Base):
    def __init__(self,gh:game.GH):
        Elimination_Base.__init__(self,gh)
        self.chess_puzzle_data:pandas.DataFrame = pandas.read_csv(f"{self.config['data_path']}\\{DATA_PATH}",dtype = {
            'PuzzleId' : 'string',
            'FEN' : 'string',
            'Moves' : 'string',
            'Rating' : 'int64',
            'RatingDeviation' : 'int64',
            'Popularity' : 'int64',
            'NbPlays' : 'int64',
            'Themes' : 'string',
            'GameUrl' : 'string',
            'OpeningTags' : 'string'
        })
        self.display_surface = pygame.Surface(ORIGINAL_BOARD_SIZE)
        self.display_board = chessboard.board.Board(ORIGINAL_BG_COLOR,self.display_surface)
        self.board:chess.Board = chess.Board()
        self.rating_range = RATING_RANGE
    def move_text(self,move_uci:str) -> str:
        def get_piece(uci:str) -> chess.Piece:
            return self.board.piece_at(eval(f"chess.{uci.upper()}"))
        piece:chess.Piece = get_piece(move_uci[0:2])
        if piece is None:
            self.logger.error(f"Chess move '{move_uci}' is invalid!")
        capture:chess.Piece = get_piece(move_uci[2:4])
        moves_to:str = 'moves to'
        and_text = ""

        if (piece.piece_type == chess.PAWN and #en passant
            capture is None and #not capturing
            move_uci[0] != move_uci[2]):#but moving diagonally
            and_text = " en passant"
            capture_symbol = 'p'
            if piece.color == chess.BLACK:
                capture_symbol = 'P'
            capture = chess.Piece.from_symbol(capture_symbol)

        if not capture is None:#capturing
            moves_to = f'captures {piece_name(capture.symbol())} {capture.unicode_symbol()} on'

        if (piece.piece_type == chess.PAWN and len(move_uci) == 5):#promotion
            promote = chess.Piece.from_symbol(move_uci[4])
            and_text = f" and promotes into a {piece_name(move_uci[4])} {promote.unicode_symbol()}"
        elif piece.piece_type == chess.KING and move_uci in CASTLE_UCI_DICT:
              return f"{move_uci} - *{CASTLE_UCI_DICT[move_uci]}*"

        return f"{move_uci} - {piece_name(piece.symbol())} {piece.unicode_symbol()} on {move_uci[0:2]} {moves_to} {move_uci[2:4]}{and_text}"
    def make_board_image(self) -> str:
        fen:str = self.board.fen()
        self.display_board.display_board()
        self.display_board.update_pieces(fen)
        image_bytes = pygame.image.tobytes(self.display_surface,'RGBA')
        size = self.display_surface.get_size()
        image:PIL.Image.Image = PIL.Image.frombytes("RGBA",size,image_bytes)
        image = image.crop((ORIGINAL_BOARDER_WIDTH,ORIGINAL_BOARDER_WIDTH,ORIGINAL_BOARD_SIZE[0]-ORIGINAL_BOARDER_WIDTH,ORIGINAL_BOARD_SIZE[1]-ORIGINAL_BOARDER_WIDTH))

        image = image.resize(SET_IMAGE_SIZE)
        image = PIL.ImageOps.expand(image,NEW_BOARDER_WIDTH,NEW_BOARDER_COLOR)
        cols:list[str] = list(l for l in COL_LABELS)
        rows:list[str] = list(l for l in ROW_LABELS)
        if self.display_board.flipped:
            cols.reverse()
            rows.reverse()
        drawer = PIL.ImageDraw.Draw(image)
        tile_size = int(SET_IMAGE_SIZE[0]/8)

        for i in range(NUM_TILES):
            drawer.text(#bottom
                (
                    NEW_BOARDER_WIDTH+int((i+0.5)*tile_size)-5,
                    BOTTOM_LABEL_OFFSET
                ),
                cols[i],TEXT_COLOR,
                font = PIL.ImageFont.truetype("arial.ttf",size = LABEL_FONT_SIZE),
                align = 'center',
                spacing = 0)
            drawer.text(
                (#side
                    SIDE_LABEL_OFFSET,
                    int(NEW_BOARDER_WIDTH/2+SET_IMAGE_SIZE[1] - (i+0.5)*tile_size)
                ),
                rows[i],TEXT_COLOR,
                font = PIL.ImageFont.truetype("arial.ttf",size = LABEL_FONT_SIZE),
                align = 'center',
                spacing = 0)

        file_path = self.temp_file_path('.png')
        image.save(file_path)
        return file_path
    def random_puzzle(self,rating_range:tuple[int,int] = None,popularity_range:tuple[int,int] = None) -> ChessPuzzleDict:
        if rating_range is None and popularity_range is None:
            return self.chess_puzzle_data.sample().to_dict()
        def get_diffs(puzzle:ChessPuzzleDict) ->tuple[int,int]:
            rating_diff = 0
            if not rating_range is None:
                if puzzle['Rating'] > rating_range[1]:
                    rating_diff = puzzle['Rating'] - rating_range[1]
                elif puzzle['Rating'] < rating_range[0]:
                    rating_diff = rating_range[0] - puzzle['Rating']
            popularity_diff = 0
            if not popularity_range is None:
                if puzzle['Popularity'] > popularity_range[1]:
                    popularity_diff = puzzle['Popularity'] - popularity_range[1]
                elif puzzle['Popularity'] < popularity_range[0]:
                    popularity_diff = popularity_range[0] - puzzle['Popularity']
            return (rating_diff,popularity_diff)
        puzzle:ChessPuzzleDict = None
        puzzle_diffs:tuple[int,int] = None
        data_sample:pandas.DataFrame = self.chess_puzzle_data.sample(n=NUM_TO_SAMPLE)
        for index, row in data_sample.iterrows():
            row_puzzle:ChessPuzzleDict = row.to_dict()
            row_diffs:tuple[int,int] = get_diffs(row_puzzle)
            if sum(row_diffs) == 0:
                return row_puzzle
            elif puzzle is None:
                puzzle = row_puzzle
                puzzle_diffs = row_diffs
            elif sum(row_diffs) < sum(puzzle_diffs):
                puzzle = row_puzzle
                puzzle_diffs = row_diffs
        return puzzle
    async def game_intro(self):
        await self.send(
            "# Welcome to a game of elimination chess puzzles!\n" + 
            "In this game you will be presented with chess puzzles.\n" +
            f"These puzzles will start with a chess rating between {RATING_RANGE[0]} and {RATING_RANGE[1]}, but may escalate if y'all do well.\n" +
            f"You must then pick the best move for the position out of {NUM_MOVE_OPTIONS} options that I provide you," +
            "keeping in mind that this puzzle may extend through a multi-move strategy.\n" +
            "If you pick the wrong move, you are eliminated (unless no one gets it right).\n" +
            "Last player standing wins!"
        )
    async def core_game(self, remaining_players: list[userid])->list[userid]:
        puzzle:ChessPuzzleDict = self.random_puzzle(self.rating_range,POPULARITY_RANGE)
        self.rating_range = (self.rating_range[0],self.rating_range[1]+PUZZLE_RATING_CAP_ESCALATION)
        self.board.set_fen(puzzle['FEN'])
        moves:list[str] = puzzle['Moves'].split(" ")
        oppo_color:str = COLOR_NAMES[self.board.turn]
        self.board.push_uci(moves[0])
        player_color:str = COLOR_NAMES[self.board.turn]
        if (player_color == 'black' and not self.display_board.flipped or
            player_color == 'white' and self.display_board.flipped):
            self.display_board.flip()

        move_index = 1
        await self.send(
            f"Here is the start of the puzzle! You will be playing for {player_color}.",
            attatchements_data=[self.make_board_image()]
        )

        def best_move(move_uci:str) -> bool:
            #checks if best move, puzzle allows any checkmate move to be solution, even if not the one given
            if move_uci == moves[move_index]:
                return True
            test_board = self.board.copy()
            test_board.push_uci(move_uci)
            return test_board.is_checkmate()

        while len(remaining_players) > 1:
            legal_moves:list[str] = list(move.uci() for move in self.board.legal_moves)
            move_options = (random.sample(legal_moves,k=NUM_MOVE_OPTIONS))
            if not moves[move_index] in move_options:
                move_options[random.randint(0,NUM_MOVE_OPTIONS-1)] = moves[move_index]
            option_text_list:list[str] = list(self.move_text(move_option) for move_option in move_options)
            
            responses:dict[userid,int] = await self.multiple_choice(
                f"What is the best move for {player_color} in this position?",
                who_chooses=remaining_players,
                options = option_text_list
            )

            correct_players = list(player for player in remaining_players if best_move(move_options[responses[player]]))
            incorrect_players = list(player for player in remaining_players if not player in correct_players)

            move_right_text = "No one got the move correct."
            best_move_text = f"The best move in this position for {player_color} is {self.move_text(moves[move_index])}."

            if correct_players:
                await self.eliminate_players(incorrect_players)
                remaining_players = correct_players
                move_right_text = f"{self.mention(correct_players)} got the move correct!"
            
            self.board.push_uci(moves[move_index])
            
            await self.send(
                f"{move_right_text} {best_move_text}",
                attatchements_data=[self.make_board_image()]
            )
            move_index += 1

            if move_index == len(moves):
                await self.send("And that's that for this puzzle!\nLet's do another one.")
                return
            
            mt = self.move_text(moves[move_index])
            self.board.push_uci(moves[move_index])
            
            respond_text = "responds with their best move in this position, "
            if len(list(self.board.legal_moves)) == 1:
                respond_text = "was forced to respond with "

            await self.send(
                f"The opponent, {oppo_color}, {respond_text} {mt}.",
                attatchements_data=[self.make_board_image()]
            )
            move_index += 1

        begin_text = "To finish of the puzzle:\n"
        
        while move_index != len(moves):
            move_text = self.move_text(moves[move_index])
            self.board.push_uci(moves[move_index])
            await self.send(
                f"{begin_text}{COLOR_NAMES[self.board.turn]} plays {move_text}.",
                attatchements_data=self.make_board_image()
            )
            begin_text = ""
            move_index += 1





