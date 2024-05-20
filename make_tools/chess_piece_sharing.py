from typing import Callable, Sequence, Mapping

import fairpyx
import chess

import json

PIECE_VALUES:list[float] = [0,1,3,3,5,9,4]# [None, "pawn", "knight", "bishop", "rook", "queen", "king"]
MIN_PLAYERS:int = 1
MAX_PLAYERS:int = 16

OUT_FILE = "data/chess_piece_sharing.json"

type ValueFunc = Callable[[chess.Square],float]

def generate_board_value(board:chess.Board, color: bool) -> ValueFunc:
    def simple_value(square:chess.Square) -> float:
        piece = board.piece_at(square)
        if piece is None:
            return 0#no piece
        if piece.color != color:
            return 0#other team
        return PIECE_VALUES[piece.piece_type]
    return simple_value

def generate_sharing(
        value_func:ValueFunc,
        options:Sequence[chess.Square],
        num_players:int) -> list[list[chess.Square]]:
    value_dict = {option:value_func(option) for option in options if value_func(option) > 0}
    valuations:dict[int,dict[chess.Square,float]] = {
        player:value_dict for player in range(num_players)
    }
    instance = fairpyx.Instance(valuations=valuations)
    allocation:Mapping[int,Sequence[chess.Square]] = fairpyx.divide(
        fairpyx.algorithms.iterated_maximum_matching_adjusted,
        instance=instance,
    )
    return list(
        list(allocate) for _,allocate in allocation.items()
    )

def main():
    board = chess.Board()
    values:dict[bool,dict[int,list[list[chess.Square]]]] = {}
    for color in chess.COLORS:
        values[color] = {}
        for num_players in range(MIN_PLAYERS,MAX_PLAYERS+1):
            values[color][num_players] = generate_sharing(generate_board_value(board,color),chess.SQUARES,num_players)
    print(values)
    with open(OUT_FILE,'w') as file:
        json.dump(values,file,indent=4)

if __name__ == '__main__':
    main()
