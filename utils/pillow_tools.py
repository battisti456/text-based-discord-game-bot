from math import ceil, floor
from typing import Optional

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

type Font = PIL.ImageFont.ImageFont|PIL.ImageFont.FreeTypeFont|PIL.ImageFont.TransposedFont
"all PIL.ImageFont font objects (as they do not inherit from a common class)"
type Color = tuple[int,int,int]|tuple[int,int,int,int]|str
"(R,G,B) or (R,G,B,A) or '#rrggbb' or '#rrggbbaa or 'color'"

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
