from typing import (
    Any,
    Literal,
    Optional,
    TypedDict,
    _TypedDictMeta,  # type: ignore
)

from utils.types import ChannelId, PlayerId
from utils.chess_tools import _RenderChessOptions
from ast import literal_eval

import ruamel.yaml
import ruamel.yaml.comments
from typeguard import TypeCheckError, check_type

yaml = ruamel.yaml.YAML()

LOCAL_CONFIG_FILE = "local_config.yaml"
type ConfigAction = Literal["add","set","remove"]
type ConfigName = Literal['config','games_config','discord_config','game_bases_config']
LIST_ACTIONS:list[ConfigAction] = ['add','remove']

class DiscordConfigDict(TypedDict):
    token:str
class ConfigDict(TypedDict):
    command_prefix:str
    command_users:list['PlayerId']
    main_channel_id:'ChannelId'
    players:list['PlayerId']
    temp_path:str
    data_path:str
    default_timeout:int
    default_warnings:list[int]
    profanity_threshold:float
    python_cmd:str
    main:str
    logging_level:str|int
    font:None|str
#region game specific configs
class AlteredImageGuessConfig(TypedDict):
    num_rounds:int
    min_image_size:tuple[int,int]
    num_choices:int
    zoom_crop_box_size:tuple[int,int]
    zoom_crop_box_display_size:tuple[int,int]
    zoom_crop_no_edge_portion:float
    blur_radius:float
    removal_color:tuple[int,int,int,int]
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
    num_colors_to_sample:int
    polygons_cover_portion:float
    polygons_border_size_range:tuple[float,float]
    swirl_side_exclusion_ratio:float
    swirl_rotation_scale:float
    swirl_rotation_offset:float
class ChessPuzzleEliminationConfig(TypedDict):
    data_path:str
    rating_range:Optional[tuple[int,int]]
    popularity_range:Optional[tuple[int,int]]
    num_to_sample:int
    num_move_options:int
    puzzle_rating_cap_escalation:int
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
    swap_range:tuple[int,int]
    give_avoid_options:bool
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
#endregion
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
#region game base specific settings
class ChessBaseConfig(_RenderChessOptions):
    ...
class RandomImageBaseConfig(TypedDict):
    pixabay_token:None|str
#endregion
class GameBasesConfigDict(TypedDict):
    chess_base:ChessBaseConfig
    random_image_base:RandomImageBaseConfig
CONFIG_TYPES:dict[ConfigName,_TypedDictMeta] = {
    'config' : ConfigDict,
    'games_config' : GamesConfigDict,
    'discord_config' : DiscordConfigDict
}
#region config errors
class ConfigError(Exception):
    ...
class IncoprehensibleValueString(ConfigError):
    ...
class BaseConfigDoesNotExist(ConfigError):
    ...
class BaseConfigTypeMismatch(ConfigError):
    ...
class ListValueDoesNotExist(ConfigError):
    ...
class ListValueAlreadyExists(ConfigError):
    ...
#endregion
with open(LOCAL_CONFIG_FILE,'r') as f:
    local_config:ruamel.yaml.comments.CommentedMap = yaml.load(f)

def edit(keys:list[str],action:ConfigAction,val_str:str):
    try:
        val = literal_eval(val_str)
    except ValueError:#assume meant to be str
        raise IncoprehensibleValueString(f"Input: '{val_str}' could not be interpreted. Remember if you would like to input a string to surround it with quotation marks.")
    if keys[0] not in CONFIG_TYPES:
        raise BaseConfigDoesNotExist(f"Config: {keys[0]} is not an available config to edit.")
    current:_TypedDictMeta = CONFIG_TYPES[keys[0]]
    for key in keys[1:]:
        if key in current.__annotations__:
            current = current.__annotations__[key]
        else:
            raise BaseConfigDoesNotExist(f"Key: {key} is not in Section: {current.__annotations__}")
    try:
        if action in LIST_ACTIONS:
            check_type([val],current)
        else:
            check_type(val,current)
    except TypeCheckError:
        raise BaseConfigTypeMismatch(f"Value: {val} is not allowed in Type: {current}")
    
    local:dict = local_config
    for key in keys[:-1]:
        if key not in local:
            local[key] = {}
            local = local[key]
        else:
            local = local[key]
    match action:
        case 'set':
            local[keys[-1]] = val
        case 'add':
            if keys[-1] not in local:
                local[keys[-1]] = []
            if val in local[keys[-1]]:
                raise ListValueAlreadyExists(f"Value: {val} already exists in {keys[-1]}.")
            local[keys[-1]].append(val)
        case 'remove':
            try:
                local[keys[-1]].remove(val)
            except (ValueError,KeyError):
                raise ListValueDoesNotExist(f"Value: {val} does not exist to be removed in {keys[-1]}.")
    

    with open(LOCAL_CONFIG_FILE,'w') as f:
        yaml.dump(local_config,f)
def _merge(f:dict[str,Any],t:dict[str,Any]):
    for key in f:
        if isinstance(f[key],dict):
            _merge(f[key],t[key])
        else:
            t[key] = f[key]
def merge_local(config_name:ConfigName,config:dict[str,Any]):
    if config_name in local_config:
        source = local_config[config_name]
        _merge(source,config)