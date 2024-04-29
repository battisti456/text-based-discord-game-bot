from typing import TypedDict, Optional

class AlteredImageGuessConfig(TypedDict):
    num_rounds:int
    min_image_size:tuple[int,int]
    num_choices:int
    zoom_crop_box_size:tuple[int,int]
    zoom_crop_box_display_size:tuple[int,int]
    zoom_crop_no_edge_portion:float
    blur_radius:float
    removal_color:tuple[int,int,int]
    removal_keep_portion:float
    bad_conversion_resize:float
    polka_dot_size_scalar:tuple[float,float]
    pixels_in_image_per_polka_dot:int
    pattern_radial_portion_visable:float
    pattern_radial_num_rays:int
    scribble_num_lines:int
    scribble_points_per_line:int
    scribble_width:int
    tile_ratio:float
class ChessPuzzleEliminationConfig(TypedDict):
    data_path:str
    rating_range:Optional[tuple[int,int]]
    popularity_range:Optional[tuple[int,int]]
    num_to_sample:int
    num_move_options:int
    puzzle_rating_cap_escalation:int
    set_image_size:tuple[int,int]
    text_color:tuple[int,int,int]
    new_border_width:int
    new_border_color:tuple[int,int,int]
    label_font_size:int
    last_move_highlight:tuple[int,int,int,int]
    check_highlight:tuple[int,int,int,int]
class ContainerBiddingConfig(TypedDict):
    num_containers:int
    data_path:str
    starting_money:int
    percentile_var:int
    end_of_game_interest:int
class EliminationBlackjackConfig(TypedDict):
    hand_limit:int
    num_players_per_deck:int
class EliminationLetterAdderConfig(TypedDict):
    num_letters:int
    start_letters:int
class EliminationRockPaperScissorsConfig(TypedDict):
    ...
class EliminationTriviaConfig(TypedDict):
    ...
class EmojiCommunicationConfig(TypedDict):
    num_rounds:int
    num_options:int
    points_for_guess:int
    points_per_guesser:int
    points_for_all_guess:int
    bonus_num:int
    bonus_points_per_guesser:int
    max_emoji:int
class GuessTheWordConfig(TypedDict):
    num_rounds:int
    min_word_len:int
    max_word_len:int
    num_definitions:int
    guess_feedback:bool
    length_hint:bool
class LongestWordConfig(TypedDict):
    num_letters:int
    number_of_rounds:int
    num_letters_can_refresh:int
class PredictionTexasHoldemConfig(TypedDict):
    num_rounds:int
    player_cards:int
    shared_cards:int
class TheGreatKittenRaceConfig(TypedDict):
    data_path:str
    num_obstacles:int
class TrickyTriviaConfig(TypedDict):
    points_fool:int
    points_guess:int
    num_questions:int
class GamesConfigDict(TypedDict):
    chess_puzzle_elimination:ChessPuzzleEliminationConfig
    altered_image_guess:AlteredImageGuessConfig
    container_bidding:ContainerBiddingConfig
    elimination_blackjack:EliminationBlackjackConfig
    elimination_letter_adder:EliminationLetterAdderConfig
    elimination_rock_paper_scissors:EliminationRockPaperScissorsConfig
    elimination_trivia:EliminationTriviaConfig
    emoji_communications:EmojiCommunicationConfig
    guess_the_word:GuessTheWordConfig
    longest_word:LongestWordConfig
    prediction_texas_holdem:PredictionTexasHoldemConfig
    the_great_kitten_race:TheGreatKittenRaceConfig
    tricky_trivia:TrickyTriviaConfig

games_config:GamesConfigDict = {
    "chess_puzzle_elimination": {
        'data_path':"lichess_db_puzzle.csv",
        'rating_range':(400,800),
        'popularity_range':None,
        'num_to_sample':500,
        'num_move_options':5,
        'puzzle_rating_cap_escalation':200,
        'set_image_size':(1500,1500),
        'text_color':(255,255,255),
        'new_border_width':100,
        'new_border_color':(0,0,0),
        'label_font_size':65,
        'last_move_highlight':(255,255,204,100),
        'check_highlight':(255,0,0,100)
    },
    "altered_image_guess" : {
        "num_rounds" : 5,
        "min_image_size" : (300,300),
        "num_choices" : 5,
        "zoom_crop_box_size" : (30,30),
        "zoom_crop_box_display_size": (400,400),
        "zoom_crop_no_edge_portion" : 0.2,
        "blur_radius" : 50,
        "removal_color" : (0,0,0),
        "removal_keep_portion" : 0.05,
        "bad_conversion_resize" : 0.5,
        "polka_dot_size_scalar" : (0.06,0.1),
        "pixels_in_image_per_polka_dot" : 5000,
        "pattern_radial_portion_visable": 0.2,
        "pattern_radial_num_rays" : 100,
        "scribble_num_lines" : 40,
        "scribble_points_per_line" : 10,
        "scribble_width" : 20,
        "tile_ratio" : 0.03
    },
    "container_bidding" : {
        'num_containers' : 5,
        'data_path':"container_contents.json",
        'starting_money':1000,
        'percentile_var':10,
        'end_of_game_interest':20
    },
    "elimination_blackjack" : {
        'hand_limit' : 21,
        'num_players_per_deck' : 7
    },
    "elimination_letter_adder" : {
        'num_letters' : 4,
        'start_letters' : 4
    },
    "elimination_rock_paper_scissors" : {},
    "elimination_trivia": {},
    "emoji_communications": {
        'num_rounds': 1,
        'num_options' : 5,
        'points_for_guess': 2,
        "points_per_guesser":1,
        "points_for_all_guess":1,
        "bonus_num":3,
        "bonus_points_per_guesser":2,
        "max_emoji":10
    },
    "guess_the_word" : {
        'num_rounds' : 3,
        'min_word_len' : 6,
        'max_word_len' : 12,
        'num_definitions' : 3,
        'guess_feedback' : True,
        'length_hint' : True
    },
    "longest_word" : {
        'num_letters' : 10,
        'number_of_rounds' : 3,
        'num_letters_can_refresh' : 5
    },
    "prediction_texas_holdem" : {
        'num_rounds' : 3,
        'player_cards' : 2,
        'shared_cards' : 5
    },
    "the_great_kitten_race" : {
        'data_path' : "kitten_race_obstacles.json",
        'num_obstacles' : 5
    },
    "tricky_trivia": {
        'points_fool':1,
        'points_guess':3,
        'num_questions':3
    }
}

try:
    from games_config_local import games_config as games_config_local
    for key in games_config_local:
        if key in games_config:
            games_config[key] = games_config_local[key]
except ImportError:
    ...# local config not set up