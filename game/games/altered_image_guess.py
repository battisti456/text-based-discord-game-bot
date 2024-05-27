import random
from typing import override

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFilter

from config.games_config import games_config
from game import get_logger
from game.components.game_interface import Game_Interface
from game.game_bases import Random_Image_Base, Rounds_With_Points_Base
from utils.grammar import temp_file_path
from utils.image_modification_functions import (
    black_and_white,
    blur,
    edge_highlight,
    pattern_radial_rays,
    polka_dots,
    remove_center,
    scribble,
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
    "covering the center of" : lambda image: remove_center(  # noqa: F405
        image,
        CONFIG['removal_keep_portion'],
        CONFIG['removal_color']
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

class Altered_Image_Guess(Rounds_With_Points_Base,Random_Image_Base):
    def __init__(self,gi:Game_Interface):
        Rounds_With_Points_Base.__init__(self,gi)
        Random_Image_Base.__init__(self,gi)
        self.num_rounds = NUM_ROUNDS
    @override
    async def game_intro(self):
        await self.basic_send(
            "# Welcome to a game of guess what I searched!\n" + 
            "In this game, I will search through an online image database via a random search term.\n" +
            "I will then take that image, and alter it to make it harder to guess.\n" +
            f"Then, for a point, you will attempt to correctly guess from {NUM_CHOICES} options which term I searched for.\n" +
            f"We will play {NUM_ROUNDS} rounds. Most points at the end wins!"
        )
    @override
    async def core_game(self):
        search_options:list[str] = random.sample(list(SEARCH_TOPICS),NUM_CHOICES)
        actual_search:str = search_options[random.randint(0,NUM_CHOICES-1)]
        image:PIL.Image.Image|None = None
        try:
            image = self.random_image(size=MIN_IMAGE_SIZE,search_terms=[actual_search])
        except ImageSearchException as e:
            logger.error(f"Unable to retrieve a random image using search term = {actual_search}\n{repr(e)}")
            await self.core_game()#start over
            return
        alter_method = random.choice(list(ALTER_METHODS))
        altered_image = ALTER_METHODS[alter_method](image)
        image_path = temp_file_path(".png")
        altered_path = temp_file_path(".png")
        image.save(image_path)
        altered_image.save(altered_path)

        await self.basic_send(
            f"I have found a random image from a search prompt, here is a version I have altered through {alter_method} the image.",
            attatchements_data=[altered_path]
        )
        
        responses:PlayerDict[int] = await self.basic_multiple_choice(
            "Which of these search prompts does this image correspond to?",
            search_options,
            who_chooses=self.unkicked_players,
            emojis = list(SEARCH_TOPICS[topic] for topic in search_options)
        )

        correct_players = list(player for player in self.unkicked_players if search_options[responses[player]] == actual_search)

        await self.basic_send(
            f"I actually searched for '{actual_search}'.",
            attatchements_data=[image_path]
        )

        await self.score(correct_players,1)
