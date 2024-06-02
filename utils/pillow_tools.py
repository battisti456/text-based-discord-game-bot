from typing import Any, Optional, override

import PIL.ExifTags as ExifTags  # noqa: F401
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import PIL.ImageOps
from color_tools_battisti456 import color_name, invert
from color_tools_battisti456.types import Color

type Font = PIL.ImageFont.ImageFont|PIL.ImageFont.FreeTypeFont|PIL.ImageFont.TransposedFont
"all PIL.ImageFont font objects (as they do not inherit from a common class)"
type DrawTextParameters = dict[str,Any]

FONT_START_SIZE = 1000
TREAT_TRANSPARENT_AS = (49, 51, 56)

def get_color_name(color:Color) -> str:
    """not fully implemented"""
    return color_name(color)

def _get_font(font_path:Optional[str] = None,size:Optional[float] = None) -> Font:
    if font_path is None:
        return PIL.ImageFont.load_default(size)
    else:
        if size is None:
            return PIL.ImageFont.truetype(font=font_path)
        else:
            return PIL.ImageFont.truetype(font=font_path,size=int(size))

def get_font(
        font_path:Optional[str] = None,
        text:Optional[str] = None,
        draw_text_parameters:DrawTextParameters = {},
        max_height:Optional[int] = None,
        max_width:Optional[int] = None,
        multi_line:bool = False) -> Font:
    if text == "" or text is None or (max_width is None and max_width is None):
        return _get_font(font_path)
    image = PIL.Image.new('RGBA',(1,1))
    draw = PIL.ImageDraw.ImageDraw(image)
    test_font = _get_font(font_path,FONT_START_SIZE)
    left:int
    top:int
    right:int
    bottom:int 
    if multi_line:
        raise NotImplementedError()
    else:
        left,top,right,bottom = draw.textbbox((0,0),text,test_font,**draw_text_parameters)
        height = bottom - top
        width = right-left
        h_mult = -1 if max_height is None else max_height/height
        w_mult = -1 if max_width is None else max_width/width
        mult = min(mult for mult in (h_mult,w_mult) if mult > 0)
        return _get_font(font_path,FONT_START_SIZE*mult)


"""class ExtendedImageDraw(PIL.ImageDraw.ImageDraw):
    def text_with_outline(
            self,
            xy:tuple[float,float],
            text:str,
            fill:Optional[Color] = None,
            font:Optional[Font] = None,
            anchor:Optional[str] = None,
            outline_width:Optional[float] = 1,
            outline_color:Optional[Color] = None,
            resolution:float = 0.1):
        if outline_width is not None:
            max_width = ceil(outline_width)
            draw_points:int = floor(max_width/resolution)
            offsets = set(
                (x/draw_points,y/draw_points) for x in range(-draw_points,draw_points+1) for y in range(-draw_points,draw_points +1)
                if (x/draw_points)**2 + (y/draw_points)**2 <= outline_width**2
            )
            for offset in offsets:
                self.text((xy[0]+offset[0],xy[1]+offset[1]),text,outline_color,font,anchor)
        self.text(xy,text,fill,font,anchor)"""

def get_colors(image:PIL.Image.Image,num:int = 16) -> list[tuple[Color,int]]:
    raw_colors = image.getcolors(maxcolors=image.size[0]*image.size[1]+1)
    if raw_colors is None:
        return []
    raw_colors.sort(key=lambda item: item[0],reverse=True)
    raw_colors = raw_colors[:num]
    if image.palette is not None:
        assert raw_colors is not None
        return list(
            (image.palette.colors[color],count) for count,color in raw_colors
        )
    elif raw_colors is not None:
        return list(
            (color,count) for count,color in raw_colors
            )#type:ignore
    else:
        return []
    
class Persistent_Exif_Image(PIL.Image.Image):
    @classmethod
    def from_image(cls,image:PIL.Image.Image) -> 'Persistent_Exif_Image':
        return Persistent_Exif_Image(image)
    def __init__(self,image:PIL.Image.Image,exif:PIL.Image.Exif|None = None):
        self.raw_image = image
        self._exif = exif
        if exif is not None:
            self.raw_image._exif = exif
    @override
    def __getattribute__(self, name: str) -> Any:
        if name in ('raw_image','metadata','save','_exif'):
            return object.__getattribute__(self,name)
        img:PIL.Image.Image = object.__getattribute__(self,'raw_image')
        val = getattr(img,name)
        if callable(val):
            def wrapper(*args,**kwargs):
                ret_val = val(*args,**kwargs)
                if isinstance(ret_val,PIL.Image.Image):
                    return Persistent_Exif_Image(ret_val,self._exif)
                else:
                    return ret_val
            return wrapper
        else:
            return val
    @override
    def save(self, fp, format=None, **params) -> None:
        return self.raw_image.save(fp, format, **params)

def make_accreditation(image:PIL.Image.Image) -> str|None:
    exif = image._exif
    if exif is None:
        return None
    if ExifTags.Base.Artist in exif:
        return f"Created by: {exif[ExifTags.Base.Artist]}"
    if ExifTags.Base.DocumentName in exif:
        return f"Titled: {exif[ExifTags.Base.DocumentName]}"
    if ExifTags.Base.UserComment in exif:
        return exif[ExifTags.Base.UserComment]
    
def add_accreditation(
        image:PIL.Image.Image,
        font_path:str|None = None,
        draw_text_parameters:DrawTextParameters = {},
        height:int|float = 20) -> PIL.Image.Image:
    accreditation = make_accreditation(image)
    if accreditation is None:
        return image
    
    if height > 1:
        height = int(height)
    else:
        height = int(height*image.size[1])
    to_return = image.copy()
    font = get_font(
        font_path=font_path,
        text=accreditation,
        draw_text_parameters=draw_text_parameters,
        max_height=height,
        max_width=image.size[0]
        )
    text_color = "black"
    if image.mode in ('P',):
        relevant_image = image.crop((0,image.size[1]-height,image.size[0],image.size[1]))
        color = get_colors(relevant_image)[0][0]
        text_color = invert(color)

    text_mask = PIL.Image.new(
        mode = 'RGBA',
        size = image.size,
        color = "#00000000")
    draw = PIL.ImageDraw.Draw(text_mask)
    draw.text(
        xy = (0,int(image.size[1] - height/2)),
        text = accreditation,
        fill = text_color,
        font = font,
        anchor = "lm"#left middle
    )
    inverted_image:PIL.Image.Image
    if image.mode == 'RGBA':
        r,g,b,a = image.split()
        for i in range(image.size[0]):
            for j in range(image.size[1]):
                if a.getpixel((i,j)) == 0:
                    r.putpixel((i,j),TREAT_TRANSPARENT_AS[0])
                    g.putpixel((i,j),TREAT_TRANSPARENT_AS[1])
                    b.putpixel((i,j),TREAT_TRANSPARENT_AS[2])
        inverted_image = PIL.ImageOps.invert(
            PIL.Image.merge('RGB',(r,g,b))
        )
        inverted_image = PIL.Image.merge(
            'RGBA',
            inverted_image.split()+(PIL.Image.new('L',image.size,255),))
    else:
        try:
            inverted_image = PIL.ImageOps.invert(image)
        except NotImplementedError:
            inverted_image = text_mask
    to_return.paste(
        im = inverted_image,
        box = (0,0),
        mask=text_mask
        )
    return to_return