#NEEDS TO BE TESTED
import csv
import random
from dataclasses import dataclass, fields
from random import randint
from typing import Any, Callable, Optional, Self, Sequence, override

import chess

from config.config import config
from config.games_config import games_config
from game.components.game_interface import Game_Interface
from game.components.participant import Player, mention_participants
from game.game_bases import Chess_Base, Elimination_Base
from utils.chess_tools import get_game_over_text, get_move_text

CONFIG = games_config['chess_puzzle_elimination']

DATA_PATH = config['data_path'] + "/" + CONFIG['data_path']

RATING_RANGE = CONFIG['rating_range']
POPULARITY_RANGE = CONFIG['popularity_range']
NUM_TO_SAMPLE = CONFIG['num_to_sample']

NUM_MOVE_OPTIONS = CONFIG['num_move_options']

PUZZLE_RATING_CAP_ESCALATION = CONFIG['puzzle_rating_cap_escalation']
NUMBER_OF_ROWS = CONFIG['number_of_rows']


@dataclass(frozen = True)
class Chess_Puzzle_Row:
    PuzzleId:str
    FEN:str#starting position (before first move)
    Moves:str#space separated ordered intended moves, first move by bot
    Rating:int#recommended chess rating
    RatingDeviation:int
    Popularity:int#lichess average popularity out of 100
    NbPlays:int#number of plays in lichess
    Themes:str#space separated theme tags
    GameUrl:str#lichess puzzle url
    OpeningTags:str#space separated opening tags
    @classmethod
    def _load(cls,row:Sequence[str]) -> Self:
        kwargs:dict[str,Any] = {}
        for i,field in enumerate(fields(cls)):
            typ = field.type
            if isinstance(typ,Callable):
                kwargs[field.name] = typ(row[i])
            else:
                kwargs[field.name] = row[i]
        return cls(**kwargs)

def validate_cpr(
        cpr:Chess_Puzzle_Row,
        rating_range:Optional[tuple[int,int]] = None,
        popularity_range:Optional[tuple[int,int]] = None
    ) -> bool:
    return (
        (rating_range is None or (
            cpr.Rating >= rating_range[0] and cpr.Rating <= rating_range[1]
        )) and (popularity_range is None or (
            cpr.Popularity >= popularity_range[0] and cpr.Popularity <= popularity_range[1]
        ))
    )

class Chess_Puzzle_Reader:
    def __init__(self, path:str):
        self.path = path
    def find(
            self,
            rating_range:Optional[tuple[int,int]] = None,
            popularity_range:Optional[tuple[int,int]] = None
        ) -> Chess_Puzzle_Row:
        offset = randint(0,NUMBER_OF_ROWS-1)
        with open(self.path,'r') as file:
            reader = csv.reader(file)
            for _ in range(offset):
                next(reader)
            for row in reader:
                cpr = Chess_Puzzle_Row._load(row)
                if validate_cpr(cpr,rating_range,popularity_range):
                    return cpr
        with open(self.path,'r') as file:
            reader = csv.reader(file)
            for row in reader:
                cpr = Chess_Puzzle_Row._load(row)
                if validate_cpr(cpr,rating_range,popularity_range):
                    return cpr
        return cpr

class Chess_Puzzle_Elimination(Elimination_Base,Chess_Base):
    def __init__(self,gi:Game_Interface):
        Elimination_Base.__init__(self,gi)
        Chess_Base.__init__(self,gi)
        self.cpr = Chess_Puzzle_Reader(DATA_PATH)
        self.rating_range:tuple[int,int]
        if RATING_RANGE is None:
            self.rating_range = (0,50000)#makes the range arbitrary
        else:
            self.rating_range = RATING_RANGE
    @override
    async def game_intro(self):
        await self.say(
            "# Welcome to a game of elimination chess puzzles!\n" + 
            "In this game you will be presented with chess puzzles.\n" +
            ("" if RATING_RANGE is None else f"These puzzles will start with a chess rating between {RATING_RANGE[0]} and {RATING_RANGE[1]}, but may escalate if y'all do well.\n") +
            f"You must then pick the best move for the position out of {NUM_MOVE_OPTIONS} options that I provide you," +
            "keeping in mind that this puzzle may extend through a multi-move strategy.\n" +
            "If you pick the wrong move, you are eliminated (unless no one gets it right).\n" +
            "Last player standing wins!"
        )
    @override
    async def core_round(self):
        puzzle:Chess_Puzzle_Row = self.cpr.find(self.rating_range,POPULARITY_RANGE)
        self.rating_range = (self.rating_range[0],self.rating_range[1]+PUZZLE_RATING_CAP_ESCALATION)
        self.board.set_fen(puzzle.FEN)
        moves:list[str] = puzzle.Moves.split(" ")
        opponent_color:str = chess.COLOR_NAMES[self.board.turn]
        self.board.push_uci(moves[0])
        player_color:chess.Color = self.board.turn
        player_color_name:str = chess.COLOR_NAMES[player_color]
        self.white_perspective = self.board.turn

        def get_board() -> str:
            return self.make_board_image({"white_perspective" : player_color})

        move_index = 1
        await self.send(
            text=f"Here is the start of the puzzle! You will be playing for {player_color_name}.",
            attach_files=(get_board(),)
        )

        def best_move(move_uci:str) -> bool:
            #checks if best move, puzzle allows any checkmate move to be solution, even if not the one given
            if move_uci == moves[move_index]:
                return True
            test_board = self.board.copy()
            test_board.push_uci(move_uci)
            return test_board.is_checkmate()

        while len(self.unkicked_players) > 1:
            legal_moves:list[str] = list(move.uci() for move in self.board.legal_moves)
            if len(legal_moves) < NUM_MOVE_OPTIONS:
                random.shuffle(legal_moves)
                move_options = legal_moves
            else:
                move_options = (random.sample(legal_moves,k=NUM_MOVE_OPTIONS))
                if moves[move_index] not in move_options:
                    move_options[random.randint(0,NUM_MOVE_OPTIONS-1)] = moves[move_index]
            option_text_list:list[str] = list(get_move_text(self.board,move_option) for move_option in move_options)
            #TODO #8 allowing people to see each other's answers seems to be a particular problem in this game, maybe a candidate for an embedded dropdown?
            responses:dict[Player,int] = await self.basic_multiple_choice(
                f"What is the best move for {player_color_name} in this position?",
                who_chooses=self.unkicked_players,
                options = option_text_list
            )

            correct_players = list(player for player in self.unkicked_players if best_move(move_options[responses[player]]))
            incorrect_players = list(player for player in self.unkicked_players if player not in correct_players)

            move_right_text = "No one got the move correct."
            best_move_text = f"The best move in this position for {player_color_name} is {get_move_text(self.board,moves[move_index])}."

            if correct_players:
                move_right_text = f"{mention_participants(correct_players)} got the move correct!"
            
            self.board.push_uci(moves[move_index])
            end_text = ""
            if self.board.is_game_over(claim_draw=True):
                end_text = f" This ends the game in {get_game_over_text(self.board)}."
            
            await self.send(
                text=f"{move_right_text} {best_move_text}{end_text}",
                attach_files=(get_board(),)
            )

            await self.eliminate(incorrect_players)
            
            move_index += 1

            if move_index == len(moves):
                await self.say("And that's that for this puzzle!\nLet's do another one.")
                return
            
            mt = get_move_text(self.board,moves[move_index])
            respond_text = "responds with their best move in this position, "
            if len(list(self.board.legal_moves)) == 1:
                respond_text = "was forced to respond with "
            self.board.push_uci(moves[move_index])
            end_text = ""
            if self.board.is_game_over(claim_draw=True):
                end_text = f" This ends the game in {get_game_over_text(self.board)}."

            await self.send(
                text = f"The opponent, {opponent_color}, {respond_text} {mt}.{end_text}",
                attach_files=(get_board(),)
            )
            move_index += 1

        begin_text = "To finish of the puzzle:\n"
        
        while move_index != len(moves):
            move_text = get_move_text(self.board,moves[move_index])
            self.board.push_uci(moves[move_index])
            end_text = ""
            if self.board.is_game_over(claim_draw=True):
                end_text = f" This ends the game in {get_game_over_text(self.board)}."
            await self.send(
                text = f"{begin_text}{chess.COLOR_NAMES[self.board.turn]} plays {move_text}.{end_text}",
                attach_files=(get_board(),)
            )
            begin_text = ""
            move_index += 1





