import random
from typing import override, Annotated

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFilter
from config_system_battisti456.config_item import Integer, FloatRange, Float, IntegerBox, Ratio
from color_tools_battisti456 import Color

from config import Config
from game.components.game_interface import Game_Interface
from game.components.participant import PlayerDict
from game.game_bases import Image_Search_Base, Rounds_With_Points_Base
from utils.common import random_from, random_in_range
from utils.grammar import temp_file_path
from utils.image_modification_functions import (
    black_and_white,
    blur,
    concentric_polygons,
    edge_highlight,
    pattern_radial_rays,
    polka_dots,
    remove_center,
    scribble,
    swirl_image,
    tiling,
    zoom_crop,
)
from utils.image_search import ImageSearchException
from utils.logging import get_logger
from utils.config_items import ColorConfigItem

class config(Config):
    num_rounds:Annotated[int,Integer(level=1,description='number of rounds',min_value=1)] = 10
    min_image_size:Annotated[tuple[int,int],IntegerBox(level=1,description='minimum allowed size for images',min_value=1)] = (300,300)
    num_choices:Annotated[int,Integer(level=1,description='number of emoji options provided for the altered image',min_value=2)] = 8
    zoom_crop_box_size:Annotated[tuple[int,int],Integer(level=1,description='size of the cropped image in the cropping alteration',min_value=1)] = (30,30)
    zoom_crop_box_display_size:Annotated[tuple[int,int],IntegerBox(level=1,description='size the cropped image is expanded to for viewing',min_value=1)] = (400,400)
    zoom_crop_no_edge_portion:Annotated[float,Float(level=1,description='portion of the images size that is excluded from the center of the crop',min_value=0,max_value=0.5)]
    blur_radius:Annotated[float,Float(level=1,description='blur radius applied in the gaussian blur alteration',min_value=1)] = 50
    removal_color:Annotated[Color,ColorConfigItem(level=1,description='fill cover for removals in various alterations')] = '#00000000'
    removal_keep_portion:Annotated[float,Ratio(level=1,description='what proportion of the image to keep when removing')] = 0.05
    bad_conversion_resize:Annotated[float,Ratio(level=1,description='what fraction of the original size of the image it is reduced to when shrunk and increased')] = 0.5
    polka_dot_size_scalar:Annotated[tuple[float,float],FloatRange(level=1,description='how big in pixels can the polka dots be as a fraction of the size of the image',min_value=0,max_value=1)] = (0.06,0.1)
    pixels_in_image_per_polka_dot:Annotated[int,Integer(level=1,description='number of pixels in image per polka dot',min_value=1)] = 5000
    pattern_radial_portion_visible:Annotated[float,Ratio(level=1,description='what portion of the image is kept visible')] = 0.2
    pattern_radial_num_rays:Annotated[int,Integer(level=1,description='number of rays to be put on the altered image',min_value=3)] = 100
    scribble_num_lines:Annotated[int,Integer(level=1,description='number of different scribble lines',min_value=1)] = 40
    scribble_num_points:Annotated[int,Integer(level=1,description='number of different points per line',min_value=2)] = 10
    scribble_width:Annotated[int,Integer(level=1,description='width of the scribble in pixels',min_value=1)] = 20
    tile_ratio:Annotated[float,Ratio(level=1,description='percent of the image size each tile takes up')] = 0.03
    num_colors_to_sample:Annotated[int,Integer(level=1,description='number of colors in the image to have included in color manipulations',min_value=1)]
    polygons_border_size_range:Annotated[tuple[float,float],Ratio(level=1)] = (0.05,0.2)
    polygons_cover_portion:Annotated[float,Float(level=1)] = 0.8
    swirl_side_exclusion_ratio:Annotated[float,Ratio(level=1)] = 0.25
    swirl_rotation_scale:Annotated[float,Float(level=1)] = 2
    swirl_rotation_offset:Annotated[float,Ratio(level=1)] = 0.5


logger = get_logger(__name__)


ALTER_METHODS = {#...altered through ____ the image
    "zooming into a random point on" : lambda image: zoom_crop(  # noqa: F405
        image,
        config.zoom_crop_no_edge_portion,
        config.zoom_crop_box_size,
        config.zoom_crop_box_display_size),
    "blurring" : lambda image: blur(  # noqa: F405
        image,
        config.blur_radius
    ),
    "applying a poorly implemented conversion to black and white to" : lambda image: black_and_white(  # noqa: F405
        image,
        config.bad_conversion_resize
    ),
    "applying an edge highlighting filter to" : lambda image: edge_highlight(  # noqa: F405
        image
    ),
    "removing the center of" : lambda image: remove_center(
        image = image,
        portion_keep=config.removal_keep_portion,
        fill = config.removal_color,
        shape=random.randint(0,2)#don't use shape 3, not very good
    ),
    "adding a few polygons to" : lambda image: concentric_polygons(
        image = image,
        on_off_ratio = random_in_range(*config.polygons_border_size_range),
        on_ratio=config.polygons_cover_portion,
        num_sides=random.randint(3,9),
        center = (random.random()*image.size[0],random.random()*image.size[1]),
        on_off_rotation=random.randint(0,10),
        fill = config.removal_color
    ),
    "adding polka dots to" : lambda image: polka_dots(  # noqa: F405
        image,
        config.polka_dot_size_scalar,
        config.pixels_in_image_per_polka_dot
    ),
    "adding some radial rays to" : lambda image: pattern_radial_rays(  # noqa: F405
        image,
        config.pattern_radial_portion_visible,
        config.pattern_radial_num_rays,
        config.removal_color
    ),
    "scribbling a bit on" : lambda image: scribble(  # noqa: F405
        image,
        config.scribble_num_lines,
        config.scribble_num_points,
        config.scribble_width
    ),
    "tiling" : lambda image: tiling(  # noqa: F405
        image,
        config.tile_ratio
    ),
    "swirling" : lambda image: swirl_image(
        image = image,
        step = 1,
        angle_func=lambda r:(r/max(image.size)*360*config.swirl_rotation_scale)*(random_from(image)+config.swirl_rotation_offset)*(-1 if random_from(image,1) > 0.5 else 1),
        center=tuple(#type:ignore
            random_in_range(
                image.size[i]*config.swirl_side_exclusion_ratio,
                image.size[i]*(1-config.swirl_side_exclusion_ratio))
                for i in range(2)),
        fill=config.removal_color,
        blur_radius=1
    )
}

SEARCH_TOPICS = {
    "dog" : '🐶',
    "fruit" : '🍎',
    'cat' : '🐱',
    "bird" : '🐦',
    "tree" : '🌳',
    "lake" : '🌊',
    "mountain" : '⛰️',
    "bicycle" : '🚲',
    "bug" : '🐛',
    "flower" : '🌼',
    "car" : '🚗',
    "airplane" : '✈️',
    "sunset" : '🌅',
    "ice cream" : '🍦',
    "drink" : '🍹',
    "city" : '🌆',
    "beach" : '🏖️',
    'ski' : '🎿',
    "skate" : '🛼',
    "offroad" : '🚵',
    "mushroom" : '🍄',
    "bread" : '🍞',
    "paper" : '📃',
    "clock" : '🕰️',
    "USA" : '🇺🇸',
    "fire" : '🔥',
    "star" : '⭐',
    "sun" : '☀️',
    "rocket" : '🚀',
    "shade" : '😎',
    "clown" : '🤡',
    "cowboy" : '🤠',
    "sleep" : '😴',
    "alien" : '👽',
    "evil" : '😈',
    "monkey" : '🙉',
    "rabbit" : '🐇',
    "sloth" : '🦥',
    "peacock" : '🦚',
    "crab" : '🦀',
    "bee" : '🐝',
    "canada" : '🇨🇦',
    "russia" : '🇷🇺',
    "china" : '🇨🇳',
    "france" : '🇫🇷',
    "madagascar" : '🇲🇬',
    "brazil" : '🇧🇷',
    "egypt" : '🇪🇬',
    "scarf" : '🧣',
    "dress" : '👗',
    "hat" : '👒',
    "guitar" : '🎸',
    "drum" : '🥁',
    "maraca" : '🪇',
    "bell" : '🔔',
    "knife" : '🗡️',
    "bubble" : '🫧',
    "teddy bear" : '🧸',
    "camera" : '📷',
    "gem" : '💎'
}

class Altered_Image_Guess(Rounds_With_Points_Base,Image_Search_Base):
    def __init__(self,gi:Game_Interface):
        Rounds_With_Points_Base.__init__(self,gi)
        Image_Search_Base.__init__(self,gi)
        self.num_rounds = config.num_rounds
    @override
    async def game_intro(self):
        await self.say(
            "# Welcome to a game of guess what I searched!\n" + 
            "In this game, I will search through an online image database via a random search term.\n" +
            "I will then take that image, and alter it to make it harder to guess.\n" +
            f"Then, for a point, you will attempt to correctly guess from {config.num_choices} options which term I searched for.\n" +
            f"We will play {config.num_rounds} rounds. Most points at the end wins!"
        )
    @override
    async def core_round(self):
        search_options:list[str] = random.sample(list(SEARCH_TOPICS),config.num_choices)
        actual_search:str = search_options[random.randint(0,config.num_choices-1)]
        image:PIL.Image.Image|None = None
        try:
            image = self.random_image(size=config.min_image_size,search_terms=[actual_search])
        except ImageSearchException as e:
            logger.error(f"Unable to retrieve a random image using search term = {actual_search}\n{repr(e)}")
            await self.core_round()#start over
            return
        alter_method = random.choice(list(ALTER_METHODS))
        altered_image = ALTER_METHODS[alter_method](image)

        image_path = temp_file_path(".png")
        altered_path = temp_file_path(".png")
        image.save(image_path)
        altered_image.save(altered_path)

        await self.send(
            text =f"I have found a random image from a search prompt, here is a version I have altered through {alter_method} the image.",
            attach_files=(altered_path,)
        )
        
        responses:PlayerDict[int] = await self.basic_multiple_choice(
            "Which of these search prompts does this image correspond to?",
            search_options,
            who_chooses=self.unkicked_players,
            emojis = list(SEARCH_TOPICS[topic] for topic in search_options)
        )

        correct_players = list(player for player in self.unkicked_players if search_options[responses[player]] == actual_search)

        await self.send(
            text =f"I actually searched for '{actual_search}'.",
            attach_files=(image_path,)
        )

        await self.score(correct_players,1)
