from typing import override, Mapping, Sequence

import chess

from game.components.game_interface import Game_Interface
from game.components.player_input import Player_Text_Input
from game.components.message import Message
from game.game_bases.chess_base import chess_move_validator_maker
from game.game_bases import Basic_Secret_Message_Base, Chess_Base, Team_Base
from game.utils.types import Team, PlayerDict, PlayerId
from game.utils.chess_tools import get_square_and_piece


class Chess_War(Team_Base, Basic_Secret_Message_Base, Chess_Base):
    def __init__(self,gi:Game_Interface):
        Basic_Secret_Message_Base.__init__(self,gi)
        Chess_Base.__init__(self,gi)
        self.num_teams = 2
        self.num_rounds = None
        self.player_pieces:PlayerDict[set[chess.Square]]
    def get_color(self,team:Team) -> bool:
        return chess.WHITE if self.all_teams.index(team) == 0 else chess.BLACK
    @override
    async def game_setup(self):
        await super().game_setup()
        self.player_pieces = {}
        for team in self.all_teams:
            
    @override
    async def core_player(self, team:Team, player: PlayerId):
        pieces:dict[chess.Square,chess.Piece] = {}
        for square in self.player_pieces[player]:
            piece = self.board.piece_at(square)
            assert piece is not None
            pieces[square] = piece
        inputs:list[Player_Text_Input] = []
        for square, piece in pieces.items():
            message = Message(
                content=f"Where would you like to move {get_square_and_piece(square,piece)}?"
            )
