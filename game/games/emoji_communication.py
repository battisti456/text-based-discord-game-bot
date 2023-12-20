import game
from game import userid
from game.game_bases import Secret_Message_Base,Rounds_With_Points_Base

class Emoji_Communication(Secret_Message_Base,Rounds_With_Points_Base):
    def __init__(self,gh:game.GH):
        Secret_Message_Base.__init__(self,gh)
        Rounds_With_Points_Base.__init__(self,gh)