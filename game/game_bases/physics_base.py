import functools
import math
from typing import (
    TYPE_CHECKING,
    Literal,
    Optional,
    Sequence,
    override,
    Iterator,
)
from typing_extensions import TypeVar

import PIL.Image
import PIL.ImageDraw
import pymunk
from color_tools_battisti456 import Color

from game import get_logger
from game.components.game_interface import Game_Interface
from game.game import Game
from utils.common import is_scale, random_in_range
from utils.grammar import temp_file_path

if TYPE_CHECKING:
    import pygame
    import pymunk.pygame_util

logger = get_logger(__name__)

RenderObject = TypeVar('RenderObject',bound='Physics_Base.Render_Object',default='Physics_Base.Render_Object')

DEFAULT_RUN_TIME = 10
DEFAULT_SIMULATION_TIMEOUT = 30

def shape_color(shape:pymunk.Shape,default:Color|None = None) -> Color|None:
    return default if not hasattr(shape,'color') else shape.color
def shape_vectors(shape:pymunk.Poly) -> Sequence[pymunk.Vec2d]:
    return shape.get_vertices() if not hasattr(shape,'_real_vertices') else shape._real_vertices

def draw_shape(
        shape:pymunk.Shape,
        image:PIL.Image.Image,*,
        border_color:Color = 'black',
        border_width:float = 0) -> PIL.Image.Image:
        image = image.copy()
        draw = PIL.ImageDraw.Draw(image)
        if isinstance(shape,pymunk.Circle):
            draw.ellipse(
                (
                    shape.body.position[0]-shape.radius+shape.offset[0],
                    shape.body.position[1]-shape.radius+shape.offset[1],
                    shape.body.position[0]+shape.radius+shape.offset[0],
                    shape.body.position[1]+shape.radius+shape.offset[1]
                ),
                fill = shape_color(shape),
                outline=border_color,
                width=int(border_width)
            )
        elif isinstance(shape,pymunk.Poly):
            vertices = tuple(
                vertex.rotated(shape.body.angle) + shape.body.position for vertex in shape.get_vertices()
            )
            draw.polygon(
                xy = vertices,
                fill = shape_color(shape),
                outline=border_color,
                width=int(border_width))
        return image
def point_contained_in(point:pymunk.Vec2d,bb:tuple[float,float,float,float],segments:Sequence[tuple[float,float,float,float]]) -> bool:
    """returns weather a given point is contained within a shape, based on a post by Gareth Rees on stack overflow: https://stackoverflow.com/questions/563198/how-do-you-detect-where-two-line-segments-intersect

    Args:
        point: the point in question
        bb: the bounding box of the shape, top, left, bottom, right
        segments: the shape defined as a sequence of line segments (x0,y0,x1,y1), should be closed

    Returns:
        weather the point is contained or not
    """
    top, left, bottom, right = bb
    q = point
    s = pymunk.Vec2d(left-1,top+1) - q
    count:int = 0
    for x0,y0,x1,y1 in segments:
        p = pymunk.Vec2d(x0,y0)
        r = pymunk.Vec2d(x1,y1)-p
        rs = r.cross(s)
        qpr = (q-p).cross(r)
        t = (q-p).cross(s/rs)
        u = (q-p).cross(r/rs)
        if rs == 0 and qpr == 0:
            #colinear
            count += 1
        elif rs == 0 and qpr != 0:
            #parallel
            pass
        elif rs != 0 and is_scale(t) and is_scale(u):
            #intersect
            count += 1
        else:
            #do not intersect in range
            pass
    return count%2 == 1

def closest_contact(point:pymunk.Vec2d,segments:Sequence[tuple[float,float,float,float]]) -> float:
    min_radius:float|None = None
    for x0,y0,x1,y1 in segments:
        r0 = pymunk.Vec2d(x0,y0)
        r1 = pymunk.Vec2d(x1,y1)
        v01 = r1-r0
        v0p = point-r0
        d = v01.dot(v0p)/abs(v01)
        segment_radius:float
        if d > abs(v01):#distance to closest point
            segment_radius = min(abs(v0p),abs(point-r1))
        else:#distance to line
            segment_radius = math.sqrt(abs(v0p)**2-d**2)
        if min_radius is None:
            min_radius = segment_radius
        else:
            if segment_radius < min_radius:
                min_radius = segment_radius
    if min_radius is None:
        raise Exception("segments was empty")
    return min_radius
def bounding_box(vertices:Sequence[tuple[float,float]]) -> tuple[float,float,float,float]:
    top:float = vertices[0][1]
    bottom:float = vertices[0][1]
    left:float = vertices[0][0]
    right:float = vertices[0][0]
    for x,y in vertices:
        if x < left:
            left = x
        if x > right:
            right = x
        if y > top:
            top = y
        if y < bottom:
            bottom = y
    return top,left,bottom,right
def vertices_to_segments(vertices:Sequence[tuple[float,float]]) -> tuple[tuple[float,float,float,float],...]:
    return tuple(
        (
            vertices[i][0],
            vertices[i][1],
            vertices[(i+1)%len(vertices)][0],
            vertices[(i+1)%len(vertices)][1]
        ) for i in range(len(vertices))
    )

class Physics_Base(Game):
    class Render_Object():
        class Shape_Holder(set[pymunk.Shape]):
            def __init__(self,ro:'Physics_Base.Render_Object'):
                self.ro = ro
                super().__init__()
            @override
            def add(self, element: pymunk.Shape) -> None:
                element.elasticity = self.ro.elasticity
                element.friction = self.ro.friction
                #element.color = self.ro.color
                element.collision_type = self.ro.collision_type
                element.ro = self.ro
                return super().add(element)
        class Position_Buffer():
            def __init__(self,max_size:int):
                self.max_size = max_size
                self._stored_values:list[pymunk.Vec2d] = []
            def average(self) -> pymunk.Vec2d:
                _sum = self._stored_values[0]
                for val in self._stored_values[1:]:
                    _sum = _sum + val
                return _sum/len(self._stored_values)
            def max_variance(self) -> float:
                avg = self.average()
                _max = abs(self._stored_values[0] - avg)
                for val in self._stored_values[1:]:
                    diff = abs(val - avg)
                    if diff > _max:
                        _max = diff
                return _max
            def __getitem__(self,i:int) -> pymunk.Vec2d:
                return self._stored_values[i]
            def __contains__(self,val:pymunk.Vec2d) -> bool:
                return val in self._stored_values
            def __iter__(self) -> Iterator[pymunk.Vec2d]:
                return self._stored_values.__iter__()
            def __len__(self) -> int:
                return len(self._stored_values)
            def update(self,val:pymunk.Vec2d):
                if len(self._stored_values) == self.max_size:
                    self._stored_values.pop(-1)
                self._stored_values.insert(0,val)
            def is_populated(self) -> bool:
                return len(self) == self.max_size
            def clear(self):
                while len(self._stored_values) > 0:
                    self._stored_values.pop(0)
            
        def __init__(
                self,*,
                buffer_size:int = 2):
            self._color:Color = '#00000000'
            self.sprite:Optional[PIL.Image.Image] = None
            self.vertices:Optional[Sequence[pymunk.Vec2d]] = None
            self.re_orient_sprite:bool = True
            self.body:pymunk.Body = pymunk.Body()
            self._init_body()
            self.shapes:set[pymunk.Shape] = Physics_Base.Render_Object.Shape_Holder(self)
            self._elasticity:float = 0
            self._friction:float = 0
            self.border_thickness:float = 0
            self.border_color:Color = 'black'
            self._collision_type:int = 0
            self.pb = Physics_Base.Render_Object.Position_Buffer(buffer_size)
        def _init_body(self):
            self.body._ro = self
            self.body.mass = 1
            self.body.moment = 1
        @property
        def collision_type(self) -> int:
            return self._collision_type
        @collision_type.setter
        def collision_type(self,val:int):
            self._collision_type = val
            for shape in self.shapes:
                shape.collision_type = val
        @property
        def color(self) -> Color:
            return self._color
        @color.setter
        def color(self,val:Color):
            self._color = val
            for shape in self.shapes:
                ...#shape.color = val
        @property
        def position(self) -> pymunk.Vec2d:
            return self.body.position
        @position.setter
        def position(self,val:tuple[float,float]):
            self.body.position = val
        @property
        def elasticity(self) -> float:
            return self._elasticity
        @elasticity.setter
        def elasticity(self,val:float):
            self._elasticity = val
            for shape in self.shapes:
                shape.elasticity = val
        @property
        def friction(self) -> float:
            return self._friction
        @friction.setter
        def friction(self,val:float):
            self._friction = val
            for shape in self.shapes:
                shape.friction = val
        
        def gen_circle(self,radius:float) -> 'Physics_Base.Render_Object':
            self.shapes.add(pymunk.Circle(
                self.body,
                radius = radius,
            ))
            return self
        def gen_bounding_box(self,vertices:Sequence[tuple[float,float]], radius:float = 0) -> 'Physics_Base.Render_Object':
            vertices = tuple(pymunk.Vec2d(*vertex) for vertex in vertices)
            self.vertices = vertices
            shape = pymunk.Poly(
                self.body,
                vertices,
                radius=radius
            )
            shape._real_vertices = vertices
            self.shapes.add(
                pymunk.Poly(
                    self.body,
                    vertices,
                    radius=radius
                )
            )
            return self
        def gen_circle_filled(
            self,
            vertices:Sequence[tuple[float,float]],
            offset:tuple[float,float] = (0,0),
            circle_density:float = 2,
            min_radius:float = 1,
            mode:Literal['grid','random'] = 'random'
            ) -> 'Physics_Base.Render_Object':
            vertices = tuple(pymunk.Vec2d(*vertex) for vertex in vertices)
            self.vertices = vertices
            bb = bounding_box(self.vertices)
            top,left,bottom,right = bb
            num_x = int((right-left)/circle_density)
            num_y = int((top-bottom)/circle_density)
            segments = vertices_to_segments(vertices)
            circles:list[tuple[float,float,float]] = []
            def point_iterator():
                match(mode):
                    case 'grid':
                        for i in range(num_x):
                            x = left + (i+0.5)*circle_density
                            for j in range(num_y):
                                y = bottom + (j+0.5)*circle_density
                                yield pymunk.Vec2d(x,y)
                    case 'random':
                        num = num_x * num_y
                        for _ in range(num):
                            yield pymunk.Vec2d(
                                random_in_range(left,right),
                                random_in_range(bottom,top)
                            )
            "radius,x,y"
            for rc in point_iterator():
                if not point_contained_in(rc,bb,segments):
                    continue
                min_radius_found:float = closest_contact(rc,segments)
                if min_radius_found < min_radius:
                    continue
                circles.append((min_radius_found,rc[0],rc[1]))
            for r,x,y in circles:
                self.shapes.add(pymunk.Circle(
                    body = self.body,
                    radius = r,
                    offset = (
                        x+offset[0],
                        y+offset[1]
                    )
                ))
            return self
        def world_vertices(self) -> tuple[pymunk.Vec2d,...]|None:
            if self.vertices is None:
                return None
            return tuple(
                vertex.rotated(self.body.angle)+self.body.position for vertex in self.vertices
            )
        def insert(self,image:PIL.Image.Image) -> PIL.Image.Image:
            pos:pymunk.Vec2d = self.body.position
            if float('nan') in pos:
                logger.warning(f"{self} has an unknown position and cannot be drawn")
                return image
            angle:float = self.body.angle
            image = image.copy()
            if self.sprite is None:
                wv = self.world_vertices()
                if wv is None:
                    for shape in self.shapes:
                        image = draw_shape(shape,image,border_color=self.border_color,border_width=self.border_thickness)
                else:
                    draw = PIL.ImageDraw.Draw(image)
                    draw.polygon(
                        wv,
                        fill = self.color,
                        outline=self.border_color,
                        width=int(self.border_thickness)
                    )
            else:
                left_corner = (
                    self.sprite.size[0] - pos[0],
                    self.sprite.size[1] - pos[1]
                )
                if not self.re_orient_sprite:
                    image.paste(
                        self.sprite,
                        box = left_corner,
                        mask = self.sprite)
                else:
                    rotated = image.rotate(
                        angle=-math.degrees(angle),
                        center=pos,
                        fillcolor='#00000000'
                    )
                    rotated.paste(self.sprite,left_corner,self.sprite)
                    rotated = rotated.rotate(
                        angle = math.degrees(angle),
                        center = pos,
                        fillcolor='#00000000'
                    )
                    image.paste(
                        rotated,
                        mask=rotated
                    )
            return image
        def link(self,space:pymunk.Space):
            space.add(self.body)
            space.add(*self.shapes)
        def unlink(self,space:pymunk.Space):
            space.remove(*self.shapes)
            space.remove(self.body)
    def __init__(self, gi: Game_Interface):
        super().__init__(gi)
        if Physics_Base not in self.initialized_bases:
            self.initialized_bases.append(Physics_Base)
            self._debug:bool = False
            self.space = pymunk.Space()
            self.time_step:float = 0.001
            self.ts_per_frame:int = 10
            self.simulation_time:float = 0
            _step = self.space.step
            @functools.wraps(self.space.step)
            def step(dt:float):
                self.simulation_time += dt
                _step(dt)
            self.space.step = step
            self.size:tuple[int,int] = (500,500)
            self._debug_surf:'pygame.Surface'
            self._debug_draw_options:pymunk.pygame_util.DrawOptions
            self.bg_color:Color = '#00000000'
            self.simulation_timeout = DEFAULT_SIMULATION_TIMEOUT
    def _enable_debug(self):
        self._debug = True
        import pygame
        import utils.pymunk_safe_pygame
        self.pygame = pygame
        self._debug_surf = self.pygame.display.set_mode(self.size,flags=self.pygame.SRCALPHA)
        self._debug_draw_options = utils.pymunk_safe_pygame.SafeDrawOptions(self._debug_surf)
    def at_simulation_pause(self) -> bool:
        if self.simulation_time - self._start_time > DEFAULT_RUN_TIME:
            return True
        return False
    def draw_space(self) -> PIL.Image.Image:
        image: PIL.Image.Image = PIL.Image.new('RGBA',self.size,self.bg_color)
        ros:tuple[Physics_Base.Render_Object,...] = tuple(
            body._ro 
            for body in self.space.bodies
            if hasattr(body,'_ro'))
        all_shapes = set(self.space.shapes)
        for ro in ros:
            all_shapes.difference_update(ro.shapes)
            image = ro.insert(image)
        for shape in all_shapes:
            image = draw_shape(shape,image)
        return image
    async def on_record_loop(self):
        for ro in self.ros():
            ro.pb.update(ro.position)
    async def record_simulation(self) -> str:
        path = temp_file_path('.gif')
        images:list[PIL.Image.Image] = []
        logger.info(f"{self} beginning to record")
        self._start_time = self.simulation_time
        while not self.at_simulation_pause():
            logger.debug(f"{self} recording loop generating new frame")
            await self.on_record_loop()
            if self._debug:
                self._debug_surf.fill(self.bg_color)
                self.space.debug_draw(self._debug_draw_options)
                self.pygame.display.flip()
            images.append(self.draw_space())
            for _ in range(self.ts_per_frame):
                self.space.step(self.time_step)
            if self.simulation_time - self._start_time > self.simulation_timeout:
                logger.warning(f"{self}'s simulation recording has timed out")
                break
        logger.info(f"{self} recording paused, now saving")
        images[0].save(
            path,
            save_all = True,
            append_images=images[1:],
            duration=self.time_step*self.ts_per_frame*1000,#duration of each frame
            transparency=0,
            loop=1,#num of times to loop, 0 for forever
            disposal=2#https://groups.google.com/g/borland.public.delphi.graphics/c/ex6WrnhZaJM
        )
        logger.info(f"{self} recording saved at '{path}'")
        return path
    def ros(self) -> Iterator[Render_Object]:
        for body in self.space.bodies:
            if hasattr(body,'_ro'):
                yield body._ro
    def coords_to_pixels(self,coords:pymunk.Vec2d) -> tuple[int,int]:
        return (int(coords[0]),self.size[1] - int(coords[1]))
    def pixels_to_coords(self,pixels:tuple[int,int]) -> pymunk.Vec2d:
        return pymunk.Vec2d(pixels[0],self.size[1]-pixels[1])

    