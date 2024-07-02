import random
from typing import override

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFilter

from config.games_config import games_config
from game import get_logger
from game.components.game_interface import Game_Interface
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
from utils.types import PlayerDict

logger = get_logger(__name__)


CONFIG = games_config['altered_image_guess']
NUM_ROUNDS = CONFIG['num_rounds']
MIN_IMAGE_SIZE = CONFIG['min_image_size']
NUM_CHOICES = CONFIG['num_choices']


ALTER_METHODS = {#...altered through ____ the image
    "zooming into a random point on" : lambda image: zoom_crop(  # noqa: F405
        image,
        CONFIG['zoom_crop_no_edge_portion'],
        CONFIG['zoom_crop_box_size'],
        CONFIG['zoom_crop_box_display_size']),
    "blurring" : lambda image: blur(  # noqa: F405
        image,
        CONFIG['blur_radius']
    ),
    "applying a poorly implemented conversion to black and white to" : lambda image: black_and_white(  # noqa: F405
        image,
        CONFIG['bad_conversion_resize']
    ),
    "applying an edge highlighting filter to" : lambda image: edge_highlight(  # noqa: F405
        image
    ),
    "removing the center of" : lambda image: remove_center(
        image = image,
        portion_keep=CONFIG['removal_keep_portion'],
        fill = CONFIG['removal_color'],
        shape=random.randint(0,2)#don't use shape 3, not very good
    ),
    "adding a few polygons to" : lambda image: concentric_polygons(
        image = image,
        on_off_ratio = random_in_range(*CONFIG['polygons_border_size_range']),
        on_ratio=CONFIG['polygons_cover_portion'],
        num_sides=random.randint(3,9),
        center = (random.random()*image.size[0],random.random()*image.size[1]),
        on_off_rotation=random.randint(0,10),
        fill = CONFIG['removal_color']
    ),
    "adding polka dots to" : lambda image: polka_dots(  # noqa: F405
        image,
        CONFIG['polka_dot_size_scalar'],
        CONFIG['pixels_in_image_per_polka_dot']
    ),
    "adding some radial rays to" : lambda image: pattern_radial_rays(  # noqa: F405
        image,
        CONFIG['pattern_radial_portion_visable'],
        CONFIG['pattern_radial_num_rays'],
        CONFIG['removal_color']
    ),
    "scribbling a bit on" : lambda image: scribble(  # noqa: F405
        image,
        CONFIG['scribble_num_lines'],
        CONFIG['scribble_points_per_line'],
        CONFIG['scribble_width']
    ),
    "tiling" : lambda image: tiling(  # noqa: F405
        image,
        CONFIG['tile_ratio']
    ),
    "swirling" : lambda image: swirl_image(
        image = image,
        step = 1,
        angle_func=lambda r:(r/max(image.size)*360*CONFIG['swirl_rotation_scale'])*(random_from(image)+CONFIG['swirl_rotation_offset'])*(-1 if random_from(image,1) > 0.5 else 1),
        center=tuple(#type:ignore
            random_in_range(
                image.size[i]*CONFIG['swirl_side_exclusion_ratio'],
                image.size[i]*(1-CONFIG['swirl_side_exclusion_ratio']))
                for i in range(2)),
        fill=CONFIG['removal_color'],
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
        self.num_rounds = NUM_ROUNDS
    @override
    async def game_intro(self):
        await self.say(
            "# Welcome to a game of guess what I searched!\n" + 
            "In this game, I will search through an online image database via a random search term.\n" +
            "I will then take that image, and alter it to make it harder to guess.\n" +
            f"Then, for a point, you will attempt to correctly guess from {NUM_CHOICES} options which term I searched for.\n" +
            f"We will play {NUM_ROUNDS} rounds. Most points at the end wins!"
        )
    @override
    async def core_round(self):
        search_options:list[str] = random.sample(list(SEARCH_TOPICS),NUM_CHOICES)
        actual_search:str = search_options[random.randint(0,NUM_CHOICES-1)]
        image:PIL.Image.Image|None = None
        try:
            image = self.random_image(size=MIN_IMAGE_SIZE,search_terms=[actual_search])
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
