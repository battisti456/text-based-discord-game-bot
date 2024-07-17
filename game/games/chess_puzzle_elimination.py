#NEEDS TO BE TESTED
import random
from typing import Optional, TypedDict, override

import chess
import pandas

from config.config import config
from config.games_config import games_config
from game.components.game_interface import Game_Interface
from game.game_bases import Chess_Base, Elimination_Base
from utils.chess_tools import get_game_over_text, get_move_text
from game.components.participant import Player, mention_participants

CONFIG = games_config['chess_puzzle_elimination']

DATA_PATH = config['data_path'] + "/" + CONFIG['data_path']

RATING_RANGE = CONFIG['rating_range']
POPULARITY_RANGE = CONFIG['popularity_range']
NUM_TO_SAMPLE = CONFIG['num_to_sample']

NUM_MOVE_OPTIONS = CONFIG['num_move_options']

PUZZLE_RATING_CAP_ESCALATION = CONFIG['puzzle_rating_cap_escalation']


#PuzzleId,FEN,Moves,Rating,RatingDeviation,Popularity,NbPlays,Themes,GameUrl,OpeningTags
class ChessPuzzleDict(TypedDict):
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

def correct_chess_puzzle(value:dict) -> ChessPuzzleDict:
    if isinstance(value['PuzzleId'],dict):
        num = list(value['PuzzleId'])[0]
        for item in value:
            value[item] = value[item][num]
    assert not isinstance(value['PuzzleId'],dict)
    return  {
        'PuzzleId' : value['PuzzleId'],
        'FEN' : value['FEN'],
        'Moves' : value['Moves'],
        'Rating' : value['Rating'],
        'RatingDeviation' : value['RatingDeviation'],
        'Popularity' : value['Popularity'],
        'NbPlays' : value['NbPlays'],
        'Themes' : value['Themes'],
        'GameUrl' : value['GameUrl'],
        'OpeningTags' : value['OpeningTags']
    }


class Chess_Puzzle_Elimination(Elimination_Base,Chess_Base):
    def __init__(self,gi:Game_Interface):
        Elimination_Base.__init__(self,gi)
        Chess_Base.__init__(self,gi)
        self.chess_puzzle_data:pandas.DataFrame = pandas.read_csv(f"{DATA_PATH}",dtype = {
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
        self.rating_range:tuple[int,int]
        if RATING_RANGE is None:
            self.rating_range = (0,50000)#makes the range arbitrary
        else:
            self.rating_range = RATING_RANGE
    def random_puzzle(self,rating_range:Optional[tuple[int,int]] = None,popularity_range:Optional[tuple[int,int]] = None) -> ChessPuzzleDict:
        if rating_range is None and popularity_range is None:
            return correct_chess_puzzle(self.chess_puzzle_data.sample().to_dict())
        def get_diffs(puzzle:ChessPuzzleDict) ->tuple[int,int]:
            rating_diff = 0
            if rating_range is not None:
                if puzzle['Rating'] > rating_range[1]:
                    rating_diff = puzzle['Rating'] - rating_range[1]
                elif puzzle['Rating'] < rating_range[0]:
                    rating_diff = rating_range[0] - puzzle['Rating']
            popularity_diff = 0
            if popularity_range is not None:
                if puzzle['Popularity'] > popularity_range[1]:
                    popularity_diff = puzzle['Popularity'] - popularity_range[1]
                elif puzzle['Popularity'] < popularity_range[0]:
                    popularity_diff = popularity_range[0] - puzzle['Popularity']
            return (rating_diff,popularity_diff)
        puzzle:ChessPuzzleDict = correct_chess_puzzle(self.chess_puzzle_data.sample().to_dict())
        puzzle_diffs:tuple[int,int] = get_diffs(puzzle)
        data_sample:pandas.DataFrame = self.chess_puzzle_data.sample(n=NUM_TO_SAMPLE)
        for _, row in data_sample.iterrows():
            row_puzzle:ChessPuzzleDict = correct_chess_puzzle(row.to_dict())
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
        puzzle:ChessPuzzleDict = self.random_puzzle(self.rating_range,POPULARITY_RANGE)
        self.rating_range = (self.rating_range[0],self.rating_range[1]+PUZZLE_RATING_CAP_ESCALATION)
        self.board.set_fen(puzzle['FEN'])
        moves:list[str] = puzzle['Moves'].split(" ")
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





