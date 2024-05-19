from typing import override

from game.components.game_interface import Game_Interface
from game.game_bases import Basic_Secret_Message_Base, Chess_Base


class Chess_War(Basic_Secret_Message_Base,Chess_Base):
    def __init__(self,gi:Game_Interface):
        Basic_Secret_Message_Base.__init__(self,gi)
        Chess_Base.__init__(self,gi)
    @override
    async def _run(self):
        ...