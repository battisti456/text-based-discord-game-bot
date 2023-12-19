import game
from game import userid
from game.game_bases import Rounds_With_Points_Base,Random_Image_Base

import random
import math
import PIL.Image
import PIL.ImageFilter
import PIL.ImageDraw

NUM_ROUNDS = 5
MIN_IMAGE_SIZE = (300,300)
NUM_CHOICES = 5
ZOOM_CROP_BOX_SIZE = (30,30)
ZOOM_CROP_BOX_DISPLAY_SIZE = (400,400)
ZOOM_CROP_NO_EDGE_PORTION = 0.2
BLUR_RADIUS = 50
REMOVAL_COLOR = (0,0,0)
REMOVAL_KEEP_PORTION = 0.05
BAD_CONVERSION_RESIZE = 0.5

POLKA_DOT_SIZE_SCALAR = (0.06,0.1)
PIXELS_IN_IMAGE_PER_POLKA_DOT = 5000
PATTERN_RADIAL_PORTION_VISABLE = 0.2
PATTERN_RADIAL_NUM_RAYS = 100

def zoom_crop(image:PIL.Image.Image) -> PIL.Image.Image:
    zoom_range:tuple[int,int,int,int] = (
        int(image.size[0]*ZOOM_CROP_NO_EDGE_PORTION),#tl x
        int(image.size[1]*ZOOM_CROP_NO_EDGE_PORTION),#tl y
        int(image.size[0]*(1-ZOOM_CROP_NO_EDGE_PORTION)),#br x
        int(image.size[1]*(1-ZOOM_CROP_NO_EDGE_PORTION))#br y
        )
    zoom_center = (
        random.randint(zoom_range[0],zoom_range[2]),
        random.randint(zoom_range[1],zoom_range[3])
    )
    zoom_crop = (
        zoom_center[0] - ZOOM_CROP_BOX_SIZE[0],
        zoom_center[1] - ZOOM_CROP_BOX_SIZE[1],
        zoom_center[0] + ZOOM_CROP_BOX_SIZE[0],
        zoom_center[1] + ZOOM_CROP_BOX_SIZE[1]
    )
    return image.crop(zoom_crop).resize(ZOOM_CROP_BOX_DISPLAY_SIZE)
def blur(image:PIL.Image.Image) -> PIL.Image.Image:
    return image.filter(PIL.ImageFilter.GaussianBlur(radius = BLUR_RADIUS))
def black_and_white(image:PIL.Image.Image) -> PIL.Image.Image:
    image = image.resize((int(image.size[0]*BAD_CONVERSION_RESIZE),int(image.size[1]*BAD_CONVERSION_RESIZE)))
    sum_all_values:int = 0
    for i in range(image.size[0]):
        for j in range(image.size[1]):
            sum_all_values += sum(image.getpixel((i,j)))
    avg_color = sum_all_values/image.size[0]/image.size[1]
    for i in range(image.size[0]):
        for j in range(image.size[1]):
            cord = (i,j)
            pixel = image.getpixel(cord)
            if sum(pixel)<avg_color:
                image.putpixel(cord,(0,0,0))
            else:
                image.putpixel(cord,(255,255,255))
    image = image.resize((int(image.size[0]/BAD_CONVERSION_RESIZE),int(image.size[1]/BAD_CONVERSION_RESIZE)))
    return image
def remove_center(image:PIL.Image.Image) -> PIL.Image.Image:
    image = image.copy()
    draw = PIL.ImageDraw.Draw(image)
    rectangle = (
        int(image.size[0]*REMOVAL_KEEP_PORTION),
        int(image.size[1]*REMOVAL_KEEP_PORTION),
        int(image.size[0]*(1-REMOVAL_KEEP_PORTION)),
        int(image.size[1]*(1-REMOVAL_KEEP_PORTION)),
    )
    circle = (
        int(image.size[0]/2),
        int(image.size[1]/2),
        min(image.size)/2
    )
    edge_rectangle = (
        0,
        0,
        image.size[0],
        image.size[1]
    )
    i = random.randint(0,3)
    if i == 0:
        draw.rectangle(rectangle,fill = REMOVAL_COLOR)
    elif i == 1:
        draw.rounded_rectangle(rectangle,radius = min(image.size)/4,fill = REMOVAL_COLOR)
    elif i == 2:
        draw.ellipse(edge_rectangle,fill = REMOVAL_COLOR)
    elif i == 3:
        draw.regular_polygon(circle,n_sides=random.randint(3,10),fill=REMOVAL_COLOR)

    return image
def edge_highlight(image:PIL.Image.Image) -> PIL.Image.Image:
    return image.filter(
        PIL.ImageFilter.Kernel(
            (3,3),
            (-1, -1, -1, -1, 11, -2, -2, -2, -2),
            1,0
        )
    )
def polka_dots(image:PIL.Image.Image) -> PIL.Image.Image:
    polka_dot_size_min:float = int(POLKA_DOT_SIZE_SCALAR[0]*min(image.size))
    polka_dot_size_max:float = int(POLKA_DOT_SIZE_SCALAR[1]*min(image.size))
    num_dots = int(image.size[0]*image.size[1]/PIXELS_IN_IMAGE_PER_POLKA_DOT)
    image = image.copy()
    draw:PIL.ImageDraw.ImageDraw = PIL.ImageDraw.Draw(image)
    for i in range(num_dots):
        radius = random.randint(polka_dot_size_min,polka_dot_size_max)
        center = (
            random.randint(0,image.size[0]-1),
            random.randint(0,image.size[1]-1)
        )
        box = (
            center[0]-radius,
            center[1]-radius,
            center[0]+radius,
            center[1]+radius
        )
        color = (
            random.randint(0,255),
            random.randint(0,255),
            random.randint(0,255)
        )
        draw.ellipse(box,color)
    return image
def pattern_radial_rays(image:PIL.Image.Image) -> PIL.Image.Image:
    image = image.copy()
    draw = PIL.ImageDraw.Draw(image)
    center = (
        random.randint(0,image.size[0]),
        random.randint(0,image.size[1])
    )
    off_angle = math.pi*(1-PATTERN_RADIAL_PORTION_VISABLE)/PATTERN_RADIAL_NUM_RAYS*2
    on_angle = math.pi*PATTERN_RADIAL_PORTION_VISABLE/PATTERN_RADIAL_NUM_RAYS*2
    radius = max(image.size)*2#guaranteed to be way to big for the image
    current_angle = 0
    for i in range(PATTERN_RADIAL_NUM_RAYS):
        draw.polygon(
            (
                center,
                (center[0] + math.cos(current_angle)*radius,center[1] + math.sin(current_angle)*radius),
                (center[0] + math.cos(current_angle+off_angle)*radius, center[1] + math.sin(current_angle+off_angle)*radius)
            ),
            fill = REMOVAL_COLOR
        )
        current_angle = current_angle + on_angle + off_angle
    return image

        

        





ALTER_METHODS = {#...altered through ____ the image
    "zooming into a random point on" : zoom_crop,
    "blurring" : blur,
    "applying a poorly implemented conversion to black and white to" : black_and_white,
    "applying an edge highlighting filter to" : edge_highlight,
    "corering the center of" : remove_center,
    "adding polka dots to" : polka_dots,
    "adding some radial rays to" : pattern_radial_rays
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
    "USA" : '🇺🇸'


}

class Altered_Image_Guess(Rounds_With_Points_Base,Random_Image_Base):
    def __init__(self,gh:game.GH):
        Rounds_With_Points_Base.__init__(self,gh)
        Random_Image_Base.__init__(self,gh)
        self.num_rounds = NUM_ROUNDS
    async def game_intro(self):
        await self.send(
            "# Welcome to a game of guess what I searched!\n" +
            "In this game, I will search through an online image database via a random search term.\n" +
            "I will then take that image, and alter it to make it harder to guess.\n" +
            f"Then, for a point, you will attempt to correctly guess from {NUM_CHOICES} options which term I searched for.\n" +
            f"We will play {NUM_ROUNDS} rounds. Most points at the end wins!"
        )
    async def core_game(self):
        search_options:list[str] = random.sample(list(SEARCH_TOPICS),NUM_CHOICES)
        actual_search:str = search_options[random.randint(0,NUM_CHOICES-1)]
        image:PIL.Image.Image = self.random_image(search_terms=[actual_search])
        while image.size[0] < MIN_IMAGE_SIZE[0] or image.size[1] < MIN_IMAGE_SIZE[1]:
            image = self.random_image(search_terms=[actual_search])
        alter_method = random.choice(list(ALTER_METHODS))
        altered_image = ALTER_METHODS[alter_method](image)
        image_path = self.temp_file_path(".jpg")
        altered_path = self.temp_file_path(".jpg")
        image.save(image_path)
        altered_image.save(altered_path)

        await self.send(
            f"I have found a random image from a search prompt, here is a version I have altered through {alter_method} the image.",
            attatchements_data=[altered_path]
        )
        
        responses = await self.multiple_choice(
            f"Which of these search prompts does this image correspond to?",
            search_options,
            emojis = list(SEARCH_TOPICS[topic] for topic in search_options)
        )

        correct_players = list(player for player in self.players if search_options[responses[player]] == actual_search)

        await self.send(
            f"I actually searched for '{actual_search}'.",
            attatchements_data=[image_path]
        )

        await self.score(correct_players,1)



    
