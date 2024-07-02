import math
import random
from typing import Literal, override, assert_never

import pymunk
from color_tools_battisti456 import Color
import PIL.Image

from game import get_logger
from game.components.game_interface import Game_Interface
from game.components.player_input import Player_Text_Input
from game.components.response_validator import text_validator_maker
from game.game_bases import Game_Word_Base, Physics_Base, Rounds_With_Points_Base
from utils.common import random_in_range
from utils.pillow_tools import center_draw_text, get_font
from utils.types import PlayerId

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
MAX_FREEZE_SPEED = 1
NUM_FROZEN_RESTING = 2
TIME_TO_START_FREEZING = 3
MIN_COLOR_MATCH = 4
MIN_WORD_LENGTH = 4
POINTS_PER_LETTER = 5
POINTS_PER_MATCH = 2
POINT_REFRESH_TIME = 1
POINT_TEXT_COLOR = '#02491f'
POINT_TEXT_OUTLINE_COLOR = '#ffffff'
POINT_TEXT_OUTLINE_WIDTH = 2

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
ANIMATION_STAGE_MAX = 10

SPRITES:tuple[PIL.Image.Image,...] = (1,)

pre_validator = text_validator_maker(
    min_length=MIN_WORD_LENGTH,
    is_alpha=True
)

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
        self.in_contact:set[Letter_RO] = set()
    def get_colored_network(self) -> frozenset['Letter_RO']:
        final_network:set[Letter_RO] = set((self,))
        checked_nodes:set[Letter_RO] = set()
        while checked_nodes != final_network:
            to_check = final_network - checked_nodes
            for node in to_check:
                to_check.update(set(
                    sub_node for sub_node in node.in_contact
                    if sub_node.letter_color == self.letter_color
                ))
                checked_nodes.add(node)
        return frozenset(final_network)
    def get_word_network(self,word:str) -> frozenset['Letter_RO']|None:
        splits = word.split(self.letter)
        if len(splits) == 1:
            return None
        left_rights:set[tuple[str,str]] = set()
        for i in range(len(splits)-1):
            left_rights.add((splits[i],splits[i+1]))
        network:set[Letter_RO] = set()
        for left_right in left_rights:
            left_right_networks = tuple(self._get_segment_network(segment) for segment in left_right)
            if None in left_right_networks:
                continue
            for sub_network in left_right_networks:
                assert sub_network is not None
                network.update(sub_network)
        if len(network) == 0:
            return None
        else:
            return frozenset(network)
    def _get_segment_network(self,segment:str) -> frozenset['Letter_RO']|None:
        if len(segment) == 0:
            return frozenset((self,))
        network:set['Letter_RO'] = set()
        for node in self.in_contact:
            if node.letter != segment[0]:
                continue
            sub_network = node._get_segment_network(segment[1:])
            if sub_network is None:
                continue
            network.update(sub_network)
        if len(network) == 0:
            return None
        else:
            return frozenset(network)
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
    def insert(self, image: PIL.Image.Image) -> PIL.Image.Image:
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

def get_letter(arbiter:pymunk.Arbiter) -> tuple[Letter_RO,Letter_RO]:
    return tuple(shape.ro for shape in arbiter.shapes)


class Letter_Physics(Physics_Base, Game_Word_Base,Rounds_With_Points_Base):
    def __init__(self, gi: Game_Interface):
        Physics_Base.__init__(self,gi)
        Game_Word_Base.__init__(self,gi)
        Rounds_With_Points_Base.__init__(self,gi)
        self.participant_round_is_concurrent = False
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
        self.___pop_animations:set[tuple[pymunk.Vec2d,Color,int]] = set()
        "x,y (in pymunk coordinates),animation_state"
        self.___current_points:int = 0
        self.___last_point_update:float|None = 0
        self.___points_overlay:PIL.Image.Image

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
            ros: tuple[Letter_RO, Letter_RO] = get_letter(arbiter)
            ros[0].in_contact.add(ros[1])
            ros[1].in_contact.add(ros[0])
            if ros[0].letter_color == ros[1].letter_color:
                network = ros[0].get_colored_network()
                if len(network) >= MIN_COLOR_MATCH:
                    self.pop_network(network,'color')
                    return
            if not self.is_freezing:
                return
            if ros[0].is_frozen == ros[1].is_frozen:
                return
            if ros[0].is_frozen:
                ros = (ros[1],ros[0])
            if ros[0].body.velocity > MAX_FREEZE_SPEED:
                return
            num_frozen = sum(int(ro.is_frozen) for ro in ros[0].in_contact)
            if num_frozen < NUM_FROZEN_RESTING:
                return
            ros[0].is_frozen = True
        self.collision_letter.begin = on_letter_collision
        def on_letter_remove_collision(_,arbiter):
            ros = get_letter(arbiter)
            ros[0].in_contact.remove(ros[1])
            ros[1].in_contact.remove(ros[0])
        self.collision_letter.separate = on_letter_remove_collision
    @override
    def on_record_loop(self):
        if self.simulation_time - self._start_time > TIME_TO_START_FREEZING:
            self.is_freezing = True
        super().on_record_loop()
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
    def reset(self):
        self.is_freezing = False
        for ro in self.ros():
            if isinstance(ro,Letter_RO):
                ro.is_frozen = False
    def match_word(self,word:str) -> frozenset[Letter_RO]:
        network:set[Letter_RO] = set()
        for node in self.ros():
            if not isinstance(node,Letter_RO):
                continue
            ret = node.get_word_network(word)
            if ret is None:
                continue
            network.update(ret)
        return frozenset(network)
    @override
    async def participant_round(self, participant: PlayerId):
        await super().participant_round(participant)
        self.reset()
        self.___current_word_network:frozenset['Letter_RO']|None = None
        def validator(_,text:str|None) -> tuple[bool,str|None]:
            pre = pre_validator(_,text)
            if not pre[0]:
                return pre
            assert text is not None
            if not self.is_valid_word(text):
                return (False,f'{text} is not a acceptable word')
            self.___current_word_network = self.match_word(text)
            if self.___current_word_network is None:
                return (False,f'{text} could not be found on screen')
            return (True,None)
        address = await self.send(
            text = f"Come on, {self.sender.format_players_md((participant,))},  give me a word!",
            hint_text="Input your word here.",
        )
        inpt = Player_Text_Input(
            "choice of word",
            self.gi,
            self.gi.default_sender,
            (participant,),
            question_address=address,
            response_validator=validator
        )
        await inpt.run()
        if self.___current_word_network is None:
            await self.kick_players((participant,),reason='timeout')
            return
        self.pop_network(self.___current_word_network,'word')
        img = self.record_simulation()
        await self.send(
            text=f"{self.format_players((participant,))}'s choice of '{inpt.responses[participant]}' resulted in:",
            attach_files=(img,)
        )
    def pop_network(self,network:frozenset[Letter_RO],pop_type:Literal['word','color']):
        num_removed = len(network)
        for ro in network:
            self.___pop_animations.add((ro.body.position,ro.letter_color,ANIMATION_STAGE_MAX))
            ro.unlink(self.space)
        match(pop_type):
            case 'word':
                self.___current_points += num_removed * POINTS_PER_LETTER
            case 'color':
                self.___current_points += num_removed * POINTS_PER_MATCH
            case _:
                assert_never(pop_type)
    @override
    def draw_space(self) -> PIL.Image.Image:
        image = super().draw_space()
        if self.___last_point_update is None or self.simulation_time - self.___last_point_update > POINT_REFRESH_TIME:
            self.___last_point_update = self.simulation_time
            self.___points_overlay = PIL.Image.new('RGBA',self.size,'#00000000')
            point_text = f"+{self.___current_points}"
            font = get_font(text=point_text,max_width=int(CENTER_RADIUS*2))
            center_draw_text(
                text = point_text,
                image = self.___points_overlay,
                xy=self.center_body.position,
                font=font,
                fill = POINT_TEXT_COLOR,
                stroke_width=POINT_TEXT_OUTLINE_WIDTH,
                stroke_fill=POINT_TEXT_OUTLINE_COLOR
            )
        for position,color,state in self.___pop_animations:
            ...
        image.paste(self.___points_overlay,mask=self.___points_overlay)
        return image



def compare(pos1:tuple[float,float],pos2:tuple[float,float]) -> bool:
    return abs(pos1[0]-pos2[0]) < COMPARE_THRESHOLD and abs(pos1[1] - pos2[1]) < COMPARE_THRESHOLD