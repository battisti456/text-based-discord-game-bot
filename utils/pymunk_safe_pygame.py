import logging
from typing import Literal, override
import time

import pygame
import pymunk
import pymunk.pygame_util
from pymunk.space_debug_draw_options import SpaceDebugColor
from color_tools_battisti456 import Color, color_to_tuple_rgb

logger = logging.getLogger(__name__)

LOG_ERROR_FREQUENCY = 5

type DrawIssue = Literal[
    'position_is_nan'
]

class SafeDrawOptions(pymunk.pygame_util.DrawOptions):
    def __init__(self, surface: pygame.Surface) -> None:
        super().__init__(surface)
        self.___current_issues:dict[DrawIssue,int] = {}
        self.___last_log:float = 0
    def ___issue(self,issue:DrawIssue):
        if issue not in self.___current_issues:
            self.___current_issues[issue] = 1
        else:
            self.___current_issues[issue] += 1
        t = time.time()
        if t - self.___last_log > LOG_ERROR_FREQUENCY:
            self.___last_log = time.time()
            logger.warning(str(self.___current_issues))
            self.___current_issues = {}
    @override
    def draw_circle(self, pos: pymunk.Vec2d, angle: float, radius: float, outline_color: Color|SpaceDebugColor, fill_color: Color|SpaceDebugColor) -> None:
        if not self.___is_safe_pos(pos):
            self.___issue('position_is_nan')
            return
        outline_color = self.___safe_color(outline_color)
        fill_color = self.___safe_color(outline_color)
        return super().draw_circle(
            pos, 
            angle, 
            radius, 
            outline_color,
            fill_color
            )
    @staticmethod
    def ___safe_color(color:Color|SpaceDebugColor) -> SpaceDebugColor:
        if isinstance(color,SpaceDebugColor):
            return color
        return SpaceDebugColor(*color_to_tuple_rgb(color))
    @staticmethod
    def ___is_safe_pos(pos:pymunk.Vec2d) -> bool:
        try:
            int(pos[0])
            int(pos[1])
            return True
        except ValueError:
            return False
        