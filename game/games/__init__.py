from random import choice

from game.game import Game
from game.games.altered_image_guess import Altered_Image_Guess
from game.games.basic_game import Basic_Game
from game.games.chess_puzzle_elimination import Chess_Puzzle_Elimination
from game.games.container_bidding import Container_Bidding
from game.games.elimination_blackjack import Elimination_Blackjack
from game.games.elimination_rock_paper_scissors import Elimination_Rock_Paper_Scissors
from game.games.elimination_trivia import Elimination_Trivia
from game.games.emoji_communication import Emoji_Communication
from game.games.guess_the_word import Guess_The_Word
from game.games.longest_word import Longest_Word
from game.games.prediction_texas_holdem import Prediction_Texas_Holdem
from game.games.the_great_kitten_race import The_Great_Kitten_Race
from game.games.tricky_trivia import Tricky_Trivia
from game.games.chess_war import Chess_War
from game.games.letter_physics import Letter_Physics

valid_games:list[type[Game]] = [
    Elimination_Blackjack,
    Elimination_Trivia,
    Longest_Word,
    Tricky_Trivia,
    Guess_The_Word,
    Elimination_Rock_Paper_Scissors,
    Container_Bidding,
    The_Great_Kitten_Race,
    Prediction_Texas_Holdem,
    Chess_Puzzle_Elimination,
    Altered_Image_Guess,
    Emoji_Communication,
    Letter_Physics]

def random_game() -> type[Game]:
    return choice(valid_games)

def search_games(name:str) -> type[Game]:
    for game_name in __all__:
        value = eval(game_name)
        if not name_comparison(game_name,name):
            continue
        if value == Game:
            raise IndexError("The base 'Game' is not meant to be played directly.")
        elif issubclass(value,Game):
            return value
        else:
            continue
    raise IndexError(f"Game '{name}' does not exist.")

def name_comparison(game_name:str,name:str) -> bool:
    game_name = game_name.lower()
    name = name.lower()
    if game_name == name:
        return True
    letters = "".join(part[0] for part in game_name.split('_'))
    if letters == name:
        return True
    return False
__all__ = (
    'Elimination_Blackjack',
    'Elimination_Trivia',
    'Longest_Word',
    'Tricky_Trivia',
    'Guess_The_Word',
    'Elimination_Rock_Paper_Scissors',
    'Container_Bidding',
    'The_Great_Kitten_Race',
    'Prediction_Texas_Holdem',
    'Chess_Puzzle_Elimination',
    'Altered_Image_Guess',
    'Emoji_Communication',
    'Basic_Game',
    'Chess_War',
    'Letter_Physics'
)