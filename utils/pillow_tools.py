from math import ceil, floor
from typing import Any, Optional

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

type Font = PIL.ImageFont.ImageFont|PIL.ImageFont.FreeTypeFont|PIL.ImageFont.TransposedFont
"all PIL.ImageFont font objects (as they do not inherit from a common class)"
type Color = tuple[int,int,int]|tuple[int,int,int,int]|str
"(R,G,B) or (R,G,B,A) or '#rrggbb' or '#rrggbbaa or 'color'"

FONT_START_SIZE = 1000

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
        draw_text_parameters:dict[str,Any] = {},
        max_height:Optional[int] = None,
        max_width:Optional[int] = None,
        multi_line:bool = False) -> Font:
    if text is None or (max_width is None and max_width is None):
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


class ExtendedImageDraw(PIL.ImageDraw.ImageDraw):
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
        self.text(xy,text,fill,font,anchor)
