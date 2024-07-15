import math
from typing import override, Literal, get_args
import random
from time import time

import pymunk

from game import get_logger
from game.components.game_interface import Game_Interface
from game.game_bases import Physics_Base
from utils.common import random_in_range
from utils.generate_vertices import star_vertices, heart_vertices

logger = get_logger(__name__)

SIZE:tuple[int,int] = (1000,1000)
CENTER_RADIUS:float = 75
GRAVITY_CONSTANT:float = 1000000#G*m1*m2 or maybe G*m1, depending if gravity is a unit of acceleration or force in pymunk
MASS_RANGE:tuple[float,float] = (0.5,1.5)
RADIUS_RANGE:tuple[float,float] = (20,50)
ADD_SHAPE_RADIUS:float = 240
NUM_DIVS:int = 8
PUSHER_VELOCITY:float = 100
PUSHER_DESPAWN:float = 400
BODY_DESPAWN:float = 600
FRICTION:float = 100000
DAMPING:float = 0.5
COMPARE_THRESHOLD:float = 0.001
FILLET = 1
SLOP = 10000

#other shapes seem to likely to bounce
ShapeTag = Literal[
    "star",
    "circle",
]
SHAPE_TAGS:tuple[ShapeTag,...] = get_args(ShapeTag)

class Shaped_RO(Physics_Base.Render_Object):
    def __init__(self):
        super().__init__()
        self.shape_tag:ShapeTag = random.choice(SHAPE_TAGS)
        self.outer_radius = random_in_range(*RADIUS_RANGE)
        match(self.shape_tag):
            case "circle":
                self.gen_circle(self.outer_radius)
            case "star":
                self.gen_bounding_box(
                    star_vertices(
                        inner_radius=self.outer_radius/2,
                        outer_radius=self.outer_radius,
                        num_points=5,
                    )
                )
            case "heart":
                self.gen_circle_filled(
                    heart_vertices(
                        curve_radius=self.outer_radius/2,
                        point_height=self.outer_radius
                    )
                )

class Wheel_Of_Shapes(Physics_Base):
    def __init__(self, gi: Game_Interface):
        super().__init__(gi)
        self.size = SIZE
        self.center_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.center_body.position = pymunk.Vec2d(self.size[0]/2,self.size[1]/2)
        self.center_shape = pymunk.Circle(
            body = self.center_body,
            radius = CENTER_RADIUS)
        self.center_shape.friction = FRICTION
        self.center_gravity = GRAVITY_CONSTANT
        self.r0:pymunk.Vec2d = self.center_body.position
        self.space.add(self.center_body,self.center_shape)
        self.num_divs = NUM_DIVS
        self.div_angle = math.pi*2/self.num_divs
        self.div_offset:float = random_in_range(0,self.div_angle)
        self.pusher_r = math.tan(self.div_angle/2)*CENTER_RADIUS
        self.space.damping = DAMPING
        self._last_positions:dict[pymunk.Body,tuple[float,float]] = {}
        self.space.collision_slop = SLOP
    def add_physics_shape(self,pos:tuple[float,float]):
        ro = Shaped_RO()
        ro.elasticity = 0
        ro.friction = 1
        ro.body.mass = random_in_range(*MASS_RANGE)
        ro.body.position = pos
        ro.body.velocity_func = self.point_gravity
        ro.link(self.space)
        def should_remove(*args,**kwargs):
            r1:pymunk.Vec2d = ro.body.position
            dr = self.r0 - r1
            d = abs(dr)
            if d > BODY_DESPAWN or math.isnan(d):
                logger.warning("FORCED TO DELETE A SHAPE FOR EXITING BOUNDS")
                ro.unlink(self.space)
            self.space.add_post_step_callback(should_remove,ro.body)
        self.space.add_post_step_callback(should_remove,ro.body)
    def add_shapes_around(self,num:int=1):
        spawn_div = math.pi*2/num
        offset = random_in_range(0,spawn_div)
        for i in range(num):
            angle = offset + spawn_div*i
            pos = (
                self.center_body.position[0]+math.sin(angle)*ADD_SHAPE_RADIUS,
                self.center_body.position[1]+math.cos(angle)*ADD_SHAPE_RADIUS
            )
            self.add_physics_shape(pos)
    def spawn_pusher(self,i:int):
        body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        body.position = self.center_body.position
        shape = pymunk.Circle(
            body = body,
            radius = self.pusher_r
        )
        angle = self.div_angle*(i+0.5)+self.div_offset
        v:pymunk.Vec2d = pymunk.Vec2d(
            math.sin(angle),
            math.cos(angle)
        )
        body.velocity = tuple(v*PUSHER_VELOCITY)
        self.space.add(body,shape)
        def should_delete(*args,**kwargs):
            r1:pymunk.Vec2d = body.position
            dr = self.r0 - r1
            d = abs(dr)
            if d > PUSHER_DESPAWN:
                self.space.remove(body,shape)
        self.space.add_post_step_callback(should_delete,body)
    def point_gravity(self,body:pymunk.Body,gravity:tuple[float,float],damping:float,dt:float):
        #is gravity a unit of force or of acceleration in this module
        r1:pymunk.Vec2d = body.position
        dr = self.r0 - r1
        d = abs(dr)
        g = dr/d*self.center_gravity/d**2
        pymunk.Body.update_velocity(body,g,damping,dt)
    @override
    def at_simulation_pause(self) -> bool:
        if not hasattr(self,'_start_time'):
            self._start_time:float = time()
        if time() - self._start_time:
            return False
        ret_val:bool = True
        for body in self.space.bodies:
            if body.body_type is pymunk.Body.DYNAMIC:
                new_pos:tuple[float,float] = tuple(body.position)#type:ignore
                if body in self._last_positions:
                    ret_val = ret_val and compare(new_pos,self._last_positions[body])
                else:
                    ret_val = False
                self._last_positions[body] = new_pos
        if ret_val:
            del self._start_time
        return ret_val


def compare(pos1:tuple[float,float],pos2:tuple[float,float]) -> bool:
    return abs(pos1[0]-pos2[0]) < COMPARE_THRESHOLD and abs(pos1[1] - pos2[1]) < COMPARE_THRESHOLD