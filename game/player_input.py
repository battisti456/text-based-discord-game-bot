from game.sender import Sender

class Player_Input(object):
    def __init__(self, sender:Sender):
        self.sender = sender
    async def run(self):
        pass
class Player_Text_Input(Player_Input):
    def __init__(self, sender:Sender):
        Player_Input.__init__(self,sender)
class Player_Multiple_Input(Player_Input):
    def __init__(self, sender:Sender):
        Player_Input.__init__(self,sender)
class Multiple_Player_Inputs(Player_Input):
    def __init__(self,sender:Sender,player_inputs:list[Player_Input]):
        Player_Input.__init__(self,sender)
        self.player_inputs = player_inputs