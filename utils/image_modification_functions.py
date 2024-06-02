import random
import math

import numpy as np
import PIL.Image
import PIL.ImageFilter
import PIL.ImageDraw
from color_tools_battisti456.types import Color

from utils.pillow_tools import get_colors

def zoom_crop(
        image:PIL.Image.Image,
        zoom_crop_edge_exclusion_ratio:float,
        zoom_size:tuple[int,int],
        out_size:tuple[int,int]) -> PIL.Image.Image:
    """accepts an image and formats a zoomed in version to return

    Args:
        image: the image to zoom in on
        zoom_crop_edge_exclusion_ratio: a value between 0 and 1 representing the portion of the image on the edge which cannot be the center of the crop
        zoom_size: the box size of the zoom in the original image
        out_size: the final out size of the zoomed in image

    Returns:
        a zoomed in version of the original image
    """
    zoom_range:tuple[int,int,int,int] = (
        int(image.size[0]*zoom_crop_edge_exclusion_ratio),#tl x
        int(image.size[1]*zoom_crop_edge_exclusion_ratio),#tl y
        int(image.size[0]*(1-zoom_crop_edge_exclusion_ratio)),#br x
        int(image.size[1]*(1-zoom_crop_edge_exclusion_ratio))#br y
        )
    zoom_center = (
        random.randint(zoom_range[0],zoom_range[2]),
        random.randint(zoom_range[1],zoom_range[3])
    )
    zoom_crop = (
        zoom_center[0] - zoom_size[0],
        zoom_center[1] - zoom_size[1],
        zoom_center[0] + zoom_size[0],
        zoom_center[1] + zoom_size[1]
    )
    return image.crop(zoom_crop).resize(out_size)
def blur(
        image:PIL.Image.Image,
        blur_radius:float
        ) -> PIL.Image.Image:
    """accepts an image and returns a blurred version

    Args:
        image: the image to blur
        blur_radius: the radius in pixels to use in the gaussian blur of the image

    Returns:
        the blurred version of the original image
    """
    return image.filter(PIL.ImageFilter.GaussianBlur(radius = int(blur_radius)))
def black_and_white(
        image:PIL.Image.Image,
        resize_factor:float) -> PIL.Image.Image:
    """returns a black and white version of the image with a low quality conversion

    Args:
        image: the image to convert to black and white
        resize_factor: a value between 0 and 1 which is what portion of the original image definition is kept during the conversion

    Returns:
        the black and white version of the original
    """
    image = image.resize((int(image.size[0]*resize_factor),int(image.size[1]*resize_factor)))
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
    image = image.resize((int(image.size[0]/resize_factor),int(image.size[1]/resize_factor)))
    return image
def remove_center(
        image:PIL.Image.Image,
        portion_keep:float,
        fill:Color,
        shape:int) -> PIL.Image.Image:
    """accepts an image and modifies it by removing a center portion

    Args:
        image: image to modify
        portion_keep: a value between 0 and 1 representing what portion of the edge is kept
        fill: color to fill the removed portion with
        shape: which shape to paste in the center of the image (0 - rectangle, 1 - rounded rectangle, 2 - ellipse, 3 - polygon)

    Returns:
        the image with the center removed
    """
    image = image.copy()
    draw = PIL.ImageDraw.Draw(image)
    rectangle = (
        int(image.size[0]*portion_keep),
        int(image.size[1]*portion_keep),
        int(image.size[0]*(1-portion_keep)),
        int(image.size[1]*(1-portion_keep)),
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
    match(shape):
        case 0:
            draw.rectangle(rectangle,fill = fill)
        case 1:
            draw.rounded_rectangle(rectangle,radius = int(min(image.size)/4),fill = fill)
        case 2:
            draw.ellipse(edge_rectangle,fill = fill)
        case 3:
            draw.regular_polygon(circle,n_sides=random.randint(3,10),fill=fill)
    return image
def edge_highlight(image:PIL.Image.Image) -> PIL.Image.Image:
    return image.filter(
        PIL.ImageFilter.Kernel(
            (3,3),
            (-1, -1, -1, -1, 11, -2, -2, -2, -2),
            1,0
        )
    )
def polka_dots(
        image:PIL.Image.Image,
        dot_min_max_scalar:tuple[float,float],
        pixels_per_dot:int,) -> PIL.Image.Image:
    """modifies an image by adding polka dots from the image's color palette

    Args:
        image: image to modify
        dot_min_max_scalar: values between 0 and 1 representing what portion of the image's size the polka dot's diameter spans
        pixels_per_dot: number of pixels in the image for each dot

    Returns:
        the image with polka dots pated on
    """
    polka_dot_size_min:float = int(dot_min_max_scalar[0]*min(image.size))
    polka_dot_size_max:float = int(dot_min_max_scalar[1]*min(image.size))
    num_dots = int(image.size[0]*image.size[1]/pixels_per_dot)
    image = image.copy()
    draw:PIL.ImageDraw.ImageDraw = PIL.ImageDraw.Draw(image)

    colors_and_weights = get_colors(image)
    indexes = np.array(range(len(colors_and_weights)))
    weights = np.array(list(weight for _,weight in colors_and_weights))
    weights = weights/sum(weights)
    for _ in range(num_dots):
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
        color = colors_and_weights[np.random.choice(indexes,p=weights)][0]
        draw.ellipse(box,color)
    return image
def pattern_radial_rays(
        image:PIL.Image.Image,
        portion_visible:float,
        num_rays:int,
        fill:Color) -> PIL.Image.Image:
    """modifies image by radially pasting blocking sections around a center point

    Args:
        image: the image to modify
        portion_visible: a value between 0 and 1 representing what portion of the image to be kept visible
        num_rays: number of covered/uncovered sections around the center point
        fill: color to add in the filled section

    Returns:
        the modified image
    """
    image = image.copy()
    draw = PIL.ImageDraw.Draw(image)
    center = (
        random.randint(0,image.size[0]),
        random.randint(0,image.size[1])
    )
    off_angle = math.pi*(1-portion_visible)/num_rays*2
    on_angle = math.pi*portion_visible/num_rays*2
    radius = max(image.size)*2#guaranteed to be way to big for the image
    current_angle = 0
    for i in range(num_rays):
        draw.polygon(
            (
                center,
                (center[0] + math.cos(current_angle)*radius,center[1] + math.sin(current_angle)*radius),
                (center[0] + math.cos(current_angle+off_angle)*radius, center[1] + math.sin(current_angle+off_angle)*radius)
            ),
            fill = fill
        )
        current_angle = current_angle + on_angle + off_angle
    return image
def scribble(
        image:PIL.Image.Image,
        num_lines:int,
        points_per_line:int,
        scribble_width:int) -> PIL.Image.Image:
    """modifies an image by adding multi-segmented lines on top of it

    Args:
        image: image to modify
        num_lines: num of separate lines to add
        points_per_line: number of points per line
        scribble_width: the width, in pixels, of the drawn lines

    Returns:
        the modified image
    """
    image = image.copy()
    draw = PIL.ImageDraw.Draw(image)
    colors_and_weights = get_colors(image)
    indexes = np.array(range(len(colors_and_weights)))
    weights = np.array(list(weight for _,weight in colors_and_weights))
    weights = weights/sum(weights)
    for _ in range(num_lines):
        points = []
        for _ in range(points_per_line):
            points.append((
                random.randint(0,image.size[0]),
                random.randint(0,image.size[1])
            ))
            draw.line(
                points,
                fill = colors_and_weights[np.random.choice(indexes,p=weights)][0],
                joint = 'curve',
                width = scribble_width
            )
    return image
def tiling(
        image:PIL.Image.Image,
        tile_ratio:float) -> PIL.Image.Image:
    """modifies an image by slicing it up into tiles an rearranging them

    Args:
        image: image to modify
        tile_ratio: a value between 0 and 1 representing the ratio of the original image size the tile size will be

    Returns:
        the modified image
    """
    tile_size = (
        int(image.size[0]*tile_ratio),
        int(image.size[1]*tile_ratio)
    )
    num_tiles = (
        int(image.size[0]/tile_size[0]),
        int(image.size[1]/tile_size[1])
    )
    new_image = PIL.Image.new(
        'RGB',
        (
            tile_size[0]*num_tiles[0],
            tile_size[1]*num_tiles[1]
        )
    )
    source_boxes:list[tuple[int,int,int,int]] = []
    for i in range(num_tiles[0]):
        for j in range(num_tiles[1]):
            tile_box = (
                i*tile_size[0],
                j*tile_size[1],
                (i+1)*tile_size[0],
                (j+1)*tile_size[1]
            )
            source_boxes.append(tile_box)
    dest_boxes = source_boxes.copy()
    random.shuffle(dest_boxes)
    for k in range(len(source_boxes)):
        cropped_image = image.crop(source_boxes[k])
        new_image.paste(cropped_image,dest_boxes[k][0:2])
    
    return new_image
def concentric_polygons(
        image:PIL.Image.Image,
        on_off_ratio:float,
        on_ratio:float,
        on_off_rotation:float,
        num_sides:int,
        center:tuple[float,float],
        fill:Color) -> PIL.Image.Image:
    """modifies an image by filling it with alternating polygons (on) and polygon cutouts revealing the original image behind (off)

    Args:
        image: image to modify
        on_off_ratio: value between 0 and 1 representing what portion of the image's smallest dimension where a single on off cycle will take place
        on_ratio: value between 0 and 1 representing what portion of the overall image that will be covered (on average)
        on_off_rotation: the amount (in degrees) to rotate the polygon between operations
        num_sides: number of sides for the polygon (polygons are all regular)
        center: center point for the concentricity
        fill: color to fill the polygons with

    Returns:
        image modified with concentric polygons
    """
    min_dim = min(image.size)
    on_dist = on_off_ratio*on_ratio*min_dim
    off_dist = on_off_ratio*(1-on_ratio)*min_dim
    on_rotation = on_ratio*on_off_rotation
    off_rotation = (1-on_ratio) *on_off_rotation

    max_inner_radius = max(math.dist(center,point) for point in (
        (0,0),
        (0,image.size[1]),
        image.size,
        (image.size[0],0)
    ))
    angle = math.pi/num_sides
    max_outer_radius = max_inner_radius/math.cos(angle)

    mask = PIL.Image.new('RGBA',image.size,"#00000000")
    draw = PIL.ImageDraw.Draw(mask)
    
    current_radius = max_outer_radius
    on = True
    current_rotation:float = 0
    while current_radius > 0:
        draw.regular_polygon(
            bounding_circle=center + (current_radius,),
            n_sides=num_sides,
            rotation=int(current_rotation),
            fill="#000000ff" if not on else "#00000000",
            width=0
        )
        on = not on
        current_rotation += on_rotation if on else off_rotation
        current_radius -= on_dist if on else off_dist
    to_return  = image.copy()
    to_return.paste(
        im = PIL.Image.new("RGBA",image.size,fill),
        box = (0,0),
        mask = mask
    )
    return to_return

__all__ = [
    'zoom_crop',
    'blur',
    'black_and_white',
    'remove_center',
    'edge_highlight',
    'polka_dots',
    'pattern_radial_rays',
    'scribble',
    'tiling',
    'concentric_polygons'
]