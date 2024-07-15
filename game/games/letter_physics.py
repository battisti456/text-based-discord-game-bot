import math
import random
from typing import Literal, override, assert_never, Iterator

import pymunk
from color_tools_battisti456 import Color
import PIL.Image

from utils.logging import get_logger
from game.components.game_interface import Game_Interface
from game.components.participant import Player
from game.components.player_input import Player_Text_Input
from game.components.player_input.response_validator import text_validator_maker
from game.game_bases import Game_Word_Base, Physics_Base, Rounds_With_Points_Base
from utils.common import random_in_range
from utils.pillow_tools import center_draw_text, get_font
from utils.types import Tuple9
from utils.grammar import temp_file_path

logger = get_logger(__name__)

SIZE:tuple[int,int] = (1000,1000)
CENTER_RADIUS:float = 75
GRAVITY_CONSTANT:float = 50000000#G*m1*m2 or maybe G*m1, depending if gravity is a unit of acceleration or force in pymunk
ADD_RADIAL_RANGE:tuple[float,float] = (300,1000)
BODY_DESPAWN:float = 600
FRICTION:float = 100000
DAMPING:float = 0.75
LETTER_RADIUS:float = 40
FONT_PATH:str|None = None
MAX_FREEZE_VELOCITY = 150
NUM_FROZEN_RESTING = 2
TIME_TO_START_FREEZING = 3
MIN_COLOR_MATCH = 4
MIN_WORD_LENGTH = 3
POINTS_PER_LETTER = 5
POINTS_PER_MATCH = 2
POINT_REFRESH_TIME = 1
POINT_TEXT_COLOR = '#02491f'
POINT_TEXT_OUTLINE_COLOR = '#ffffff'
POINT_TEXT_OUTLINE_WIDTH = 2
NUM_LETTERS = 100
LOADING_PATH = 'data/loading.gif'
CONTACT_RADIUS = LETTER_RADIUS*1.05
MAX_UPDATE_ITER = 1000
DT = 0.05
ROH_SIZE = (int(SIZE[0]/CONTACT_RADIUS/2),int(SIZE[1]/CONTACT_RADIUS/2))
TIMEOUT = 45

BUFFER_SIZE = 10
MAX_VARIANCE_EXIT = 5

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

SPRITE_PATH = 'data/letter_physics_pop.png'

zero_vector = pymunk.Vec2d(0,0)

all_sprites = PIL.Image.open(SPRITE_PATH).convert('L')

sprite_size = all_sprites.size[1]
num_sprites = int(all_sprites.size[0]/sprite_size)

sprites:tuple[PIL.Image.Image,...] = tuple(
    all_sprites.crop((
        i*sprite_size,
        0,
        (i+1)*sprite_size,
        sprite_size
    ))
    for i in range(num_sprites)
)

color_images:dict[Color,PIL.Image.Image] = {
    color:PIL.Image.new(
        mode='RGBA',
        size=(sprite_size,sprite_size),
        color = color
    )
    for color in LETTER_COLORS
}

pre_validator = text_validator_maker(
    min_length=MIN_WORD_LENGTH,
    is_alpha=True
)

class Letter_RO(Physics_Base.Render_Object):
    def __init__(self,center_position:pymunk.Vec2d):
        super().__init__()
        self.letter:str = Game_Word_Base.random_balanced_letters(1)
        self.gen_circle(LETTER_RADIUS)
        self.color_index:int = random.randint(0,len(LETTER_COLORS)-1)
        self.letter_color = LETTER_COLORS[self.color_index]
        self.border_color = LETTER_COLORS[self.color_index]
        self.border_thickness = 5
        self.collision_type = LETTER_TYPE
        self.is_frozen:bool = False
        self.in_contact:set[Letter_RO] = set()
        self.center_pos:pymunk.Vec2d = center_position
    def _update(self) -> bool:
        changed:bool = False
        center_vector = self.position-self.center_pos
        froze_cross = set(
            center_vector.cross(ro.position-self.center_pos)
            for ro in self.in_contact
            if ro.is_frozen)
        num_frozen_check:bool = (
            any(cross < 0 for cross in froze_cross) 
            and any(cross > 0 for cross in froze_cross)
        )
        center_check = abs(self.position-self.center_pos) <= CONTACT_RADIUS+CENTER_RADIUS
        not_moving_check:bool
        if len(self.pb) >= 2:
            velocity = abs(self.pb[1] - self.position)/DT
            not_moving_check = velocity < MAX_FREEZE_VELOCITY
        else:
            not_moving_check = True
        if not self.is_frozen:
            if (num_frozen_check or center_check) and not_moving_check:
                self.is_frozen = True
                changed = True
        else:
            if not num_frozen_check and not center_check:
                self.is_frozen = False
                changed = True
        return changed
    @staticmethod
    def update_ros(next_to_update:set['Letter_RO']):
        ro_update:set[Letter_RO]
        update_count = 0
        while len(next_to_update) > 0:
            update_count += 1
            ro_update = next_to_update
            next_to_update = set()
            for ro in ro_update:
                if ro._update():
                    next_to_update.update(ro.in_contact)
            if update_count > MAX_UPDATE_ITER:
                logger.warning(f"letter updating exceeded max iterations of {MAX_UPDATE_ITER}")
                break
    def update(self):
        self.update_ros(set((self,)))
    def get_colored_network(self) -> frozenset['Letter_RO']:
        final_network:set[Letter_RO] = set((self,))
        checked_nodes:set[Letter_RO] = set()
        while checked_nodes != final_network:
            to_check = final_network - checked_nodes
            for node in to_check:
                final_network.update(set(
                    sub_node for sub_node in node.in_contact
                    if sub_node.letter_color == self.letter_color
                ))
                checked_nodes.add(node)
        return frozenset(final_network)
    def update_body_type(self):
        if not self.is_frozen:
            self.body.body_type = pymunk.Body.DYNAMIC
            self._init_body()
        else:
            self.body.body_type = pymunk.Body.STATIC
    def get_word_network(self,word:str,exclude:set['Letter_RO'] = set()) -> frozenset['Letter_RO']|None:
        if self in exclude:
            return None
        if word[0] != self.letter:
            return None
        if len(word) == 1:
            return frozenset((self,))
        exclude = exclude.intersection((self,))
        to_return:set[Letter_RO] = set((self,))
        for in_contact in self.in_contact:
            return_value = in_contact.get_word_network(word[1:],exclude)
            if return_value is None:
                continue
            to_return.update(return_value)
        if len(to_return) == 0:
            return None
        else:
            print(to_return)
            return frozenset(to_return)
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
        try:
            center_draw_text(
                image=image,
                xy = self.position,#type:ignore
                text = self.letter,
                font = font,
                fill=self.letter_color,
                stroke_width=1,
                stroke_fill='black'
            )
        except ValueError:#nan
            ...
        return image
    @override
    def __str__(self) -> str:
        return f"{self.__class__.__name__}{self.letter,self.letter_color}"
    @override
    def __repr__(self) -> str:
        return str(self)

class Letter_Physics(Physics_Base, Game_Word_Base,Rounds_With_Points_Base):
    class RO_Holder(dict[tuple[int,int],set[Physics_Base.Render_Object]]):
        OFFSETS:Tuple9[tuple[int,int]] = (
            (-1,-1),
            (0,-1),
            (1,-1),
            (-1,0),
            (0,0),
            (1,0),
            (-1,1),
            (0,1),
            (1,1)
        )
        def __init__(self,pb:Physics_Base):
            self.pb = pb
            self.num_square:tuple[int,int] = ROH_SIZE
            self.square_size:tuple[float,float] = (self.pb.size[0]/self.num_square[0],self.pb.size[1]/self.num_square[1])
        @override
        def __getitem__(self, key: tuple[int,int]) -> set[Physics_Base.Render_Object]:
            if key not in self.keys():
                self[key] = set()
            return super().__getitem__(key)
        def coord_to_index(self,coord:tuple[float,float]) -> tuple[int,int]:
            return (
                int(coord[0]/self.square_size[0]),
                int(coord[1]/self.square_size[1])
            )
        def index(self,ro:Physics_Base.Render_Object) -> tuple[int,int]:
            return self.coord_to_index(ro.position)
        @staticmethod
        def get_neighboring_indices(index:tuple[int,int]) -> Tuple9[tuple[int,int]]:
            return tuple(
                (index[0]+i,index[1]+j) for i,j in Letter_Physics.RO_Holder.OFFSETS#type:ignore
                )
        def get_neighbors(self,ro:Physics_Base.Render_Object) -> set[Physics_Base.Render_Object]:
            to_return:set[Physics_Base.Render_Object] = set()
            center_index = self.index(ro)
            for index in self.get_neighboring_indices(center_index):
                to_return.update(self[index])
            return to_return
        def refresh(self):
            for _set in self.values():
                _set.clear()
            for ro in self.pb.ros():
                self[self.index(ro)].add(ro)
        def remove(self,ro:Physics_Base.Render_Object):
            self[self.index(ro)].remove(ro)
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
        self.time_step = DT
        self.ts_per_frame = 5
        self.space.collision_slop = 0.2
        self.is_freezing:bool = False
        self.___pop_animations:set[tuple[pymunk.Vec2d,Color,int]] = set()
        "x,y (in pymunk coordinates),animation_state"
        self.___current_points:int = 0
        self.___last_point_update:float|None = None
        self.___points_overlay:PIL.Image.Image
        self.spawn_letters(NUM_LETTERS)
        self.ro_holder = Letter_Physics.RO_Holder(self)
        self.simulation_timeout = TIMEOUT
    def update_ro_in_contact(self):
        for ro in self.ros():
            if not isinstance(ro,Letter_RO):
                continue
            square_neighbors = self.ro_holder.get_neighbors(ro)
            ro.in_contact.clear()
            for neighbor in square_neighbors:
                if ro == neighbor:
                    continue
                if not isinstance(neighbor,Letter_RO):
                    continue
                if not abs(ro.position-neighbor.position) < CONTACT_RADIUS*2:
                    continue
                ro.in_contact.add(neighbor)
    def update_to_color_pop(self):
        to_pop:set[Letter_RO] = set()
        for ro in self.ros():
            if not isinstance(ro,Letter_RO):
                continue
            color_network = ro.get_colored_network()
            if len(color_network) >= MIN_COLOR_MATCH:
                to_pop.update(color_network)
        if to_pop:
            self.pop_network(frozenset(to_pop),'color')
    def update_ro_body_type(self):
        for ro in self.ros():
            if isinstance(ro,Letter_RO):
                ro.update_body_type()
    def update_ro_is_frozen(self):
        for ro in self.ros():
            if isinstance(ro,Letter_RO):
                ro.update()
    def add_letter(self,pos:tuple[float,float]):
        ro = Letter_RO(self.r0)
        ro.position = pos
        ro.body.velocity_func = self.point_gravity
        ro.link(self.space)
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
            if any(abs(point - ro.position) < LETTER_RADIUS*2 for ro in self.letters()):
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
    def letters(self) -> Iterator[Letter_RO]:
        return (ro for ro in self.ros() if isinstance(ro,Letter_RO))
    def reset(self):
        self.is_freezing = False
        for ro in self.ros():
            if isinstance(ro,Letter_RO):
                ro.is_frozen = False
                ro.body.body_type = pymunk.Body.DYNAMIC
                ro.pb.clear()
        self.___current_points = 0
        self.___last_point_update = None
    def match_word(self,word:str) -> frozenset[Letter_RO]|None:
        to_return:set[Letter_RO] = set()
        for letter in self.letters():
            return_value = letter.get_word_network(word)
            if return_value is None:
                continue
            to_return.update(return_value)
        if len(to_return) == 0:
            return None
        return frozenset(to_return)
    def pop_network(self,network:frozenset[Letter_RO],pop_type:Literal['word','color']):
        logger.info(f"popping {network} for '{pop_type}'")
        num_removed = len(network)
        to_update:set[Letter_RO] = set()
        for ro in network:
            self.___pop_animations.add((ro.body.position,ro.letter_color,num_sprites-1))
            ro.unlink(self.space)
            self.ro_holder.remove(ro)
            to_update.update(ro.in_contact)
        to_update = to_update - network
        Letter_RO.update_ros(to_update)
        match(pop_type):
            case 'word':
                self.___current_points += num_removed * POINTS_PER_LETTER
            case 'color':
                self.___current_points += num_removed * POINTS_PER_MATCH
            case _:
                assert_never(pop_type)
        self.spawn_letters(num_removed)
        self.update_ro_in_contact()
    #region physics base overrides
    @override
    def at_simulation_pause(self) -> bool:
        all_frozen = all(letter.is_frozen for letter in self.letters())
        if all_frozen:
            return True
        for ro in self.letters():
            if not ro.pb.is_populated():
                return False
            if ro.pb.max_variance() > MAX_VARIANCE_EXIT:
                return False
        return True
    @override
    async def record_simulation(self) -> str:
        path:str = await super().record_simulation()
        return path
    @override
    async def on_record_loop(self):
        if self.simulation_time - self._start_time > TIME_TO_START_FREEZING:
            self.is_freezing = True
        self.ro_holder.refresh()
        self.update_ro_in_contact()
        self.update_to_color_pop()
        self.update_ro_is_frozen()
        self.update_ro_body_type()
        await super().on_record_loop()
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
        for pos,color,state in self.___pop_animations:
            image.paste(
                im = color_images[color],
                box = (int(pos[0]-sprite_size/2),int(pos[1]-sprite_size/2)),
                mask = sprites[state]
            )
        self.___pop_animations = set((pos,color,state-1) for pos,color,state in self.___pop_animations if state > 0)
        image.paste(self.___points_overlay,mask=self.___points_overlay)
        return image
    #endregion
    #region game functions
    @override
    async def participant_round(self, participant: Player):
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
        display_text:str=  f"{self.format_players((participant,))}'s choice of '{inpt.responses[participant]}' resulted in:"
        display_address = await self.send(
            text=display_text,
            attach_files=(LOADING_PATH,)
        )
        img = await self.record_simulation()
        await self.send(
            address=display_address,
            text=display_text,
            attach_files=(img,)
        )
        await self.score(
            who = participant,
            amount=self.___current_points,
        )
        self.reset()
    @override
    async def game_intro(self):
        intro_text = ("# Welcome to a game with some letters and some physics!\n" +
            "For this game, on your turn, you will choose a word to pop. " +
            f"This word must contain at least {MIN_WORD_LENGTH} letter(s).\n" +
            f"Then the letters will begin falling towards the center, and any time {MIN_COLOR_MATCH} or more letters of the same color come into contact they will also pop, continuing the reaction.\n" +
            f"Pops from the word guess are {POINTS_PER_LETTER} per letter and for color matches they are {POINTS_PER_MATCH} per.\n")
        intro_address = await self.send(
            attach_files=(LOADING_PATH,),
            text = intro_text)
        
        await self.record_simulation()
        start_image = Physics_Base.draw_space(self)
        start_image_path = temp_file_path('.png')
        start_image.save(start_image_path)
        await self.send(
            address=intro_address,
            text=intro_text,
            attach_files=(start_image_path,)
        )
        return await super().game_intro()
    #endregion
