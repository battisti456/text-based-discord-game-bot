import functools
from typing import override

import imageio
import imageio.typing
import numpy as np
import pygame
import pymunk
import pymunk.pygame_util
from color_tools_battisti456 import Color

from game.components.game_interface import Game_Interface
from game.game import Game
from utils.grammar import temp_file_path

DEFAULT_RUN_TIME = 10

class Physics_Base(Game):
    def __init__(self, gi: Game_Interface):
        super().__init__(gi)
        if Physics_Base not in self.initialized_bases:
            self.initialized_bases.append(Physics_Base)
            self.space = pymunk.Space()
            self.time_step:float = 0.01
            self.ts_per_frame:int = 10
            self.simulation_time:float = 0
            self._step = self.space.step
            @functools.wraps(self.space.step)
            def step(dt:float):
                self.simulation_time += dt
                self._step(dt)
            self.space.step = step
            self.size:tuple[int,int] = (500,500)
            self.surf:pygame.Surface
            self.draw_options:pymunk.pygame_util.DrawOptions
            self.bg_color:Color = '#00000000'
    @override
    async def game_setup(self):
        await super().game_setup()
        self.surf = pygame.Surface(self.size,flags=pygame.SRCALPHA)
        self.draw_options = pymunk.pygame_util.DrawOptions(self.surf)
    def at_simulation_pause(self) -> bool:
        if not hasattr(self,'_start_time'):
            self._start_time:float = self.simulation_time
        if self.simulation_time - self._start_time > DEFAULT_RUN_TIME:
            del self._start_time
            return True
        return False
    def record_simulation(self) -> str:
        path = temp_file_path('.gif')
        frames:list[np.ndarray] = []
        while not self.at_simulation_pause():
            self.surf.fill(self.bg_color)
            self.space.debug_draw(self.draw_options)
            rgb = pygame.surfarray.pixels3d(self.surf)
            alpha = pygame.surfarray.pixels_alpha(self.surf)
            array = np.empty(self.size+(4,),dtype=np.uint8)
            array[:,:,0:3] = rgb
            array[:,:,3] = alpha
            frames.append(array)
            for _ in range(self.ts_per_frame):
                self.space.step(self.time_step)
        imageio.v3.imwrite(
            path,
            frames,
            plugin='pillow',
            mode='RGBA',
            duration=self.time_step*self.ts_per_frame*1000,#duration of each frame
            transparency=0,
            loop=1,#num of times to loop, 0 for forever
            disposal=2#https://groups.google.com/g/borland.public.delphi.graphics/c/ex6WrnhZaJM
        )
        return path

    