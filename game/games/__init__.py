from game.game import Game

from random import choice

from game.games.elimination_blackjack import Elimination_Blackjack
from game.games.elimination_trivia import Elimination_Trivia
from game.games.elimination_letter_adder import Elimination_Letter_Adder
from game.games.longest_word import Longest_Word
from game.games.tricky_trivia import Tricky_Trivia
from game.games.guess_the_word import Guess_The_Word
from game.games.elimination_rock_paper_scissors import Elimination_Rock_Paper_Scissors
from game.games.container_bidding import Container_Bidding
from game.games.the_great_kitten_race import The_Great_Kitten_Race
from game.games.prediction_texas_holdem import Prediction_Texas_Holdem
from game.games.chess_puzzle_elimination import Chess_Puzzle_Elimination
from game.games.altered_image_guess import Altered_Image_Guess
from game.games.emoji_communication import Emoji_Communication

games:list[type[Game]] = [
    Elimination_Blackjack,
    Elimination_Trivia,
    Elimination_Letter_Adder,
    Longest_Word,Tricky_Trivia,
    Guess_The_Word,
    Elimination_Rock_Paper_Scissors,
    Container_Bidding,
    The_Great_Kitten_Race,
    Prediction_Texas_Holdem,
    Chess_Puzzle_Elimination,
    Altered_Image_Guess,
    Emoji_Communication]

def random_game() -> type[Game]:
    return choice(games)

