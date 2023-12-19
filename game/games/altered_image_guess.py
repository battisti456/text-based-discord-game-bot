import game
from game import userid
from game.game_bases import Rounds_With_Points_Base,Random_Image_Base

import random
import PIL.Image
import PIL.ImageFilter
import PIL.ImageDraw

NUM_ROUNDS = 5
MIN_IMAGE_SIZE = (300,300)
NUM_CHOICES = 5
ZOOM_CROP_BOX_SIZE = (30,30)
ZOOM_CROP_NO_EDGE_PORTION = 0.2
BLUR_RADIUS = 50
REMOVAL_COLOR = (0,0,0)
REMOVAL_KEEP_PORTION = 0.3
THRESHOLD = 150

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
    return image.crop(zoom_crop)
def blur(image:PIL.Image.Image) -> PIL.Image.Image:
    return image.filter(PIL.ImageFilter.GaussianBlur(radius = BLUR_RADIUS))
def black_and_white(image:PIL.Image.Image) -> PIL.Image.Image:
    image = image.copy()
    for i in range(image.size[0]):
        for j in range(image.size[1]):
            cord = (i,j)
            pixel = image.getpixel(cord)
            if sum(pixel)<THRESHOLD:
                image.putpixel(cord,(0,0,0))
            else:
                image.putpixel(cord,(255,255,255))
    return image.convert('1')
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
    i = random.randint(0,4)
    if i == 0:
        draw.rectangle(rectangle,fill = REMOVAL_COLOR)
    elif i == 1:
        draw.rounded_rectangle(rectangle,radius = min(image.size)/4,fill = REMOVAL_COLOR)
    elif i == 2:
        draw.ellipse(rectangle,fill = REMOVAL_COLOR)
    elif i == 3:
        draw.regular_polygon(circle,n_sides=random.randint(3,10),fill=REMOVAL_COLOR)
    elif i == 4:
        reverse = random.randint(0,1)
        start = 0 + 90*reverse
        end = 180 +90*reverse
        draw.chord(rectangle,start =start, end = end,fill = REMOVAL_COLOR)
    return image
def edge_highlight(image:PIL.Image.Image) -> PIL.Image.Image:
    return image.filter(
        PIL.ImageFilter.Kernel(
            (3,3),
            (-1, -1, -1, -1, 11, -2, -2, -2, -2),
            1,0
        )
    )

ALTER_METHODS = {#...altered through a ____
    "zoom crop" : zoom_crop,
    "blur" : blur,
    "bad conversion to 1-bit" : black_and_white,
    "removal of the center" : remove_center,
    "edge highlighting fitler" : edge_highlight
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
    "offroad" : '🚵'
}

class Altered_Image_Guess(Rounds_With_Points_Base,Random_Image_Base):
    def __init__(self,gh:game.GH):
        Rounds_With_Points_Base.__init__(self,gh)
        Random_Image_Base.__init__(self,gh)
        self.num_rounds = NUM_ROUNDS
    def random_crop(self,image:PIL.Image.Image) -> PIL.Image.Image:
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
        return image.crop(zoom_crop)
    def blur(self,image:PIL.Image.Image) -> PIL.Image.Image:
        return image.filter(PIL.ImageFilter.GaussianBlur(radius = BLUR_RADIUS))
    async def core_game(self):
        search_options:list[str] = random.choices(list(SEARCH_TOPICS),k=NUM_CHOICES)
        actual_search:str = search_options[random.randint(0,NUM_CHOICES-1)]
        image:PIL.Image.Image = self.random_image(search_terms=[actual_search])
        while image.size[0] < MIN_IMAGE_SIZE[0] or image.size[1] < MIN_IMAGE_SIZE[1]:
            image = self.random_image(search_terms=[actual_search])
        alter_method = random.choice(list(ALTER_METHODS))
        altered_image = ALTER_METHODS[alter_method](image)
        image_path = self.temp_file_path("jpg")
        altered_path = self.temp_file_path("jpg")
        image.save(image_path)
        altered_image.save(altered_path)

        await self.send(
            f"I have found a random image from a search prompt, here is a version I have altered through a {alter_method}.",
            attatchements_data=[altered_path]
        )
        
        responses = await self.multiple_choice(
            f"Which of these does this image correspond to?",
            search_options,
            emojis = list(SEARCH_TOPICS[topic] for topic in search_options)
        )

        correct_players = list(player for player in self.players if responses[player] == actual_search)

        await self.send(
            f"I actually searched for '{actual_search}'.",
            attatchements_data=[image_path]
        )

        await self.score(correct_players,1)



    
