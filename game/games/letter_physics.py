import math
from typing import override
import random

from PIL.Image import Image
import pymunk
from color_tools_battisti456 import Color

from game.components.game_interface import Game_Interface
from game.game_bases import Physics_Base, Game_Word_Base
from game import get_logger
from utils.common import random_in_range
from utils.pillow_tools import get_font, center_draw_text

logger = get_logger(__name__)

SIZE:tuple[int,int] = (1000,1000)
CENTER_RADIUS:float = 75
GRAVITY_CONSTANT:float = 50000000#G*m1*m2 or maybe G*m1, depending if gravity is a unit of acceleration or force in pymunk
MASS_RANGE:tuple[float,float] = (0.5,1.5)
RADIUS_RANGE:tuple[float,float] = (20,50)
ADD_RADIAL_RANGE:tuple[float,float] = (300,1000)
NUM_DIVS:int = 8
PUSHER_VELOCITY:float = 100
PUSHER_DESPAWN:float = 400
BODY_DESPAWN:float = 600
FRICTION:float = 100000
DAMPING:float = 0.75
COMPARE_THRESHOLD:float = 0.1
LETTER_RADIUS:float = 40
FONT_PATH:str|None = None

LETTER_COLORS:tuple[Color,...] = (
    "#338731",
    "#2e652b",
    "#337a4f",
    "#2e8b74",
    "#4973ad",
    "#5972d4",
    "#474a95",
    "#6652c8",
    "#845799",
    "#9541ab")

LETTER_TYPE = 10
CENTER_TYPE = 100

class Letter_RO(Physics_Base.Render_Object):
    def __init__(self):
        super().__init__()
        self.letter:str = Game_Word_Base.random_balanced_letters(1)
        self.gen_circle(LETTER_RADIUS)
        self.color_index:int = random.randint(0,len(LETTER_COLORS)-1)
        self.letter_color = LETTER_COLORS[self.color_index]
        self.border_color = LETTER_COLORS[self.color_index]
        self.border_thickness = 5
        self.collision_type = LETTER_TYPE
        self._is_frozen:bool = False
        self.frozen_to:set[Letter_RO] = set()
    @property
    def is_frozen(self) -> bool:
        return self.is_frozen
    @is_frozen.setter
    def is_frozen(self,val:bool):
        if val:
            self.body.body_type = pymunk.Body.STATIC
        else:
            self.body.body_type = pymunk.Body.DYNAMIC
            self.frozen_to = set()
        self._is_frozen = val
    @override
    def insert(self, image: Image) -> Image:
        image = super().insert(image)
        font = get_font(
            font_path=FONT_PATH,
            text=self.letter,
            max_height=int(LETTER_RADIUS),
            max_width=int(LETTER_RADIUS)
        )
        #can add rotation later
        center_draw_text(
            image=image,
            xy = self.position,#type:ignore
            text = self.letter,
            font = font,
            fill=self.letter_color,
            stroke_width=1,
            stroke_fill='black'
        )
        return image


class Letter_Physics(Physics_Base, Game_Word_Base):
    def __init__(self, gi: Game_Interface):
        Physics_Base.__init__(self,gi)
        Game_Word_Base.__init__(self,gi)
        self.size = SIZE
        self.center_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.center_body.position = pymunk.Vec2d(self.size[0]/2,self.size[1]/2)
        self.center_shape = pymunk.Circle(
            body = self.center_body,
            radius = CENTER_RADIUS)
        self.center_shape.friction = FRICTION
        self.center_shape.collision_type = CENTER_TYPE
        self.center_gravity = GRAVITY_CONSTANT
        self.r0:pymunk.Vec2d = self.center_body.position
        self.space.add(self.center_body,self.center_shape)
        self.space.damping = DAMPING
        self._last_positions:dict[pymunk.Body,tuple[float,float]] = {}
        self.time_step = 0.05
        self.ts_per_frame = 5
        self.letters:set[Letter_RO] = set()
        self.space.collision_slop = 0.2
        self.is_freezing:bool = False

        self.collision_center =  self.space.add_collision_handler(LETTER_TYPE,CENTER_TYPE)
        def on_center_collision(_,arbiter:pymunk.Arbiter):
            if not self.is_freezing:
                return
            ro:Letter_RO
            if arbiter.shapes[0] == self.center_shape:
                ro = arbiter.shapes[1].ro
            else:
                ro = arbiter.shapes[0].ro
            ro.is_frozen = True
        self.collision_center.begin = on_center_collision
        self.collision_letter = self.space.add_collision_handler(LETTER_TYPE,LETTER_TYPE)
        def on_letter_collision(_,arbiter:pymunk.Arbiter):
            if not self.is_freezing:
                return
            ros:tuple[Letter_RO,Letter_RO] = tuple(shape.ro for shape in arbiter.shapes)
            if ros[0].is_frozen == ros[1].is_frozen:
                return#neither or both are frozen
            for i in True,False:
                ros[i].frozen_to.add(ros[not i])
                ros[i].is_frozen = True
        self.collision_letter.begin = on_letter_collision

    def add_letter(self,pos:tuple[float,float]):
        ro = Letter_RO()
        ro.position = pos
        ro.body.velocity_func = self.point_gravity
        ro.link(self.space)
        self.letters.add(ro)
    def spawn_letters(self,num:int=1):
        points:list[pymunk.Vec2d] = []
        while len(points) < num:
            r = random_in_range(*ADD_RADIAL_RANGE)
            a = random.random()*math.pi*2
            point = self.center_body.position + pymunk.Vec2d(
                r*math.cos(a),
                r*math.sin(a)
            )
            if any(abs(point-p) < LETTER_RADIUS*2 for p in points):
                continue
            if any(abs(point - ro.position) < LETTER_RADIUS*2 for ro in self.letters):
                continue
            points.append(point)
        for p in points:
            self.add_letter(p)
    def point_gravity(self,body:pymunk.Body,gravity:tuple[float,float],damping:float,dt:float):
        #is gravity a unit of force or of acceleration in this module
        r1:pymunk.Vec2d = body.position
        dr = self.r0 - r1
        d = abs(dr)
        g = dr/d*self.center_gravity/d**2
        pymunk.Body.update_velocity(body,g,damping,dt)
    @override
    def at_simulation_pause(self) -> bool:
        ...#add code for turning on freeze
        return all(letter.is_frozen for letter in self.letters)
    @override
    def record_simulation(self) -> str:
        path = super().record_simulation()
        self.is_freezing = False
        for letter in self.letters:
            letter.is_frozen = False
        return path


def compare(pos1:tuple[float,float],pos2:tuple[float,float]) -> bool:
    return abs(pos1[0]-pos2[0]) < COMPARE_THRESHOLD and abs(pos1[1] - pos2[1]) < COMPARE_THRESHOLD