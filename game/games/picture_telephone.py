from game import PlayerDict, make_player_dict
from game.game_bases import Rounds_With_Points_Base, Random_Image_Base
from game.game_interface import Game_Interface

from game.message import Message
from game.player_input import Player_Text_Input
from game.response_validator import text_validator_maker

NUM_ROUNDS = 1
MIN_NUM_WORDS = 1
MAX_NUM_WORDS = 5

validator = text_validator_maker(
    min_num_words=MIN_NUM_WORDS,
    max_num_words=MAX_NUM_WORDS,
    is_alpha=True
)

class Picture_Telephone(Rounds_With_Points_Base, Random_Image_Base):
    def __init__(self,gi:Game_Interface):
        Rounds_With_Points_Base.__init__(self,gi)
        Random_Image_Base.__init__(self,gi)
        self.num_rounds = NUM_ROUNDS
        self.text_answers:list[list[str]] = []
        self.images:list[list[str]] = []
        self.current_offset = 0
    async def game_intro(self):
        pass
    async def core_game(self) -> PlayerDict[int] | None:
        self.text_answers = list(list() for player in self.unkicked_players)
        self.images = list(list() for player in self.unkicked_players)
        self.current_offset = 0

    async def prompt_telephone(self):
        questions:PlayerDict[Message] = {}
        inputs:PlayerDict[Player_Text_Input] = {}
        for player in self.unkicked_players:
            content:str =""
            attach_paths:list[str]|None = None
            if len(self.images[0]) == 0:
                content = f"Please enter between {MIN_NUM_WORDS} and {MAX_NUM_WORDS} words."
            else:
                attach_paths = [self.images[(self.unkicked_players.index(player) + self.current_offset)%len(self.unkicked_players)][-1]]
                content = f"Please summerize this image in between {MIN_NUM_WORDS} and {MAX_NUM_WORDS} words."
            questions[player] = Message(
                content = content,
                attach_paths=attach_paths,
                players_who_can_see=[player]
            )
            inputs[player] = Player_Text_Input(
                name = f"{self.sender.format_players_md([player])}",
                gi = self.gi,
                sender = self.sender,
                players = [player],
                who_can_see=[player],
                message=questions[player],
                response_validator= validator
            )
        #do the rest!


