from game.components.interface_component import Interface_Component
from game.components.game_interface import Game_Interface

class Interface_Operator(Interface_Component):
    def __init__(self,gi:Game_Interface):
        super().__init__(gi)