from typing import TypedDict

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


class GamesConfigDict(TypedDict):
    altered_image_guess:AlteredImageGuessConfig

games_config:GamesConfigDict = {
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
    }
}

try:
    from games_config_local import games_config as games_config_local
    for key in games_config_local:
        if key in games_config:
            games_config[key] = games_config_local[key]
except ImportError:
    ...# local config not set up
