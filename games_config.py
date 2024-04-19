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
class GamesConfigDict(TypedDict):
    chess_puzzle_elimination:ChessPuzzleEliminationConfig
    altered_image_guess:AlteredImageGuessConfig
    container_bidding:ContainerBiddingConfig
    elimination_blackjack:EliminationBlackjackConfig

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
    }
}

try:
    from games_config_local import games_config as games_config_local
    for key in games_config_local:
        if key in games_config:
            games_config[key] = games_config_local[key]
except ImportError:
    ...# local config not set up
