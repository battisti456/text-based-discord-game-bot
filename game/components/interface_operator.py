from game.components.game_interface import Game_Interface
from game.components.interface_component import Interface_Component


class Interface_Operator(Interface_Component):
    def __init__(self,gi:Game_Interface):
        super().__init__(gi)
