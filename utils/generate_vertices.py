from typing import Sequence
import math

type Point = tuple[float,float]

def star_vertices(inner_radius:float,outer_radius:float,num_points:int,skew:float = 1) -> Sequence[Point]:
    vertices:list[Point] = []
    point_angle = math.pi*2/num_points
    for i in range(num_points):
        outer_angle = point_angle*i
        vertices.append((
            outer_radius*math.sin(outer_angle),
            outer_radius*math.cos(outer_angle)
        ))
        inner_angle = point_angle*(i+0.5*skew)
        vertices.append((
            inner_radius*math.sin(inner_angle),
            inner_radius*math.cos(inner_angle)
        ))
    return vertices
def heart_vertices(curve_radius:float,point_height:float,curve_resolution:int = 10) -> Sequence[Point]:
    vertices:list[Point] = []
    curve_angle = math.pi*2-math.atan(point_height/curve_radius)*2
    angle_step = curve_angle/curve_resolution

    for i in range(curve_resolution+1):
        angle = i*angle_step
        vertices.append((
            curve_radius*math.sin(angle),
            curve_radius+curve_radius*math.cos(angle)
        ))
    vertices.append((-point_height,0))
    for i in range(curve_resolution):
        angle = math.pi/4+curve_angle/2+i*angle_step
        vertices.append((
            curve_radius*math.sin(angle),
            -curve_radius+curve_radius*math.cos(angle)
        ))
    return vertices