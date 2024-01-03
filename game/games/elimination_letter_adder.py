from game.game_bases.elimination_base import Elimination_Base
from game.game_bases.dictionary_base import Dictionary_Base
from game.game_interface import Game_Interface
from game.message import Message, make_no_yes_bullet_points, make_bullet_points
from game.player_input import Player_Input, Player_Single_Choice_Input, Player_Text_Input, run_inputs
from game.response_validator import text_validator_maker

from game import PlayerId, PlayerPlacement

from typing import Iterable

import random

NUM_LETTERS = 4
START_LETTERS = NUM_LETTERS
LEFT_RIGHT_EMOJI = ['⬅️','➡️']

class Elimination_Letter_Adder(Elimination_Base,Dictionary_Base):
    def __init__(self,gi:Game_Interface):
        Elimination_Base.__init__(self,gi)
        Dictionary_Base.__init__(self,gi)
        self.last_player:PlayerId = self.players[0]
    async def game_intro(self):
        await self.basic_send(
            "# We are playing a game of word creation!\n" +
            "In this game you take turns adding letters to the combined letters, choosing to put them on the left or right side.\n" +
            f"Once we have more than {NUM_LETTERS}, if you add a letter that makes it spell a word, you lose!\n" +
            "But, beware! If the person after you challenges your word you must provide a word " + 
            "that could still be spelled with the letters, or else you are eliminated.\n" +
            "If the challenge was made in haste, however, the challenger is eliminated instead.\n" +
            f"To start us off in a round, I will generate {START_LETTERS} letters which are definitely a part of a word."
        )
    async def game_outro(self,order:PlayerPlacement):
        pass
    async def core_game(self,remaining_players:list[PlayerId]) -> list[PlayerId] | None:
        num_letters_in_starting_word = START_LETTERS + random.randint(1,len(remaining_players))
        starting_word = self.random_word(num_letters_in_starting_word)
        offset = random.randint(0,num_letters_in_starting_word-START_LETTERS-1)
        letters = starting_word[offset:offset+START_LETTERS]
        first_turn = True
        while True:
            #determine whose turn it is
            player = None
            main_index = self.players.index(self.last_player)
            for i in range(1,len(self.players)):
                player = self.players[(main_index+i)%len(self.players)]
                if player in remaining_players:
                    break
            #
            await self.basic_send(f"The letters are '{letters}'.")
            will_challenge_message = Message(
                content=f"Will you challenge {self.sender.format_players_md([self.last_player])}?",
                bullet_points=make_no_yes_bullet_points()
            )
            left_right_message = Message(
                content = "Which side would you like to put your letter on, and which letter would you like to add?",
                bullet_points=make_bullet_points(['left','right'],LEFT_RIGHT_EMOJI)
            )
            challenge_input = Player_Single_Choice_Input(
                "choice to challenge",
                self.gi,
                self.sender,
                [player],
                message=will_challenge_message
            )
            left_right_input = Player_Single_Choice_Input(
                "choice of left or right",
                self.gi,
                self.sender,
                [player],
                message = left_right_message
            )
            letter_input = Player_Text_Input(
                "choice of letter",
                self.gi,
                self.sender,
                [player],
                text_validator_maker(max_length=1,min_length=1,is_alpha=True),
                message=left_right_message
            )
            if first_turn:
                first_turn = False
                await self.sender(left_right_message)
                await run_inputs(
                    inputs = [left_right_input,letter_input],
                )
            else:
                await self.sender(will_challenge_message)
                await self.sender(left_right_message)
                await run_inputs(
                    inputs = [challenge_input,left_right_input,letter_input],
                    completion_sets= [{challenge_input},{left_right_input,letter_input}],
                )

            if not challenge_input.responses[player]:#add letter
                letter = letter_input.responses[player]
                assert not letter is None
                letter = letter.lower()
                if left_right_input.responses[player]:#1 is right
                    letters = letters + letter
                else:
                    letters = letter + letters
                if len(letters) > NUM_LETTERS and self.is_word(letters):
                    definition = self.define(letters)
                    def_text = ""
                    if not definition is None:
                        def_text = f"\nHere are some definitions:\n{self.definition_string(definition)}"
                    await self.basic_send(
                        f"{self.format_players_md([player])} has spelled the word {letters}.{def_text}")
                    self.last_player = player
                    return [player]
                else:
                    self.last_player = player
            else:#challenge
                message = Message(
                    f"{self.format_players_md([player])} has chosen to challenge {self.format_players_md([self.last_player])} on the letters '{letters}'. \n" +
                    "What word do you think you could have spelled?")
                word_input = Player_Text_Input(
                    "word",
                    self.gi,
                    self.sender,
                    [self.last_player],
                    text_validator_maker(is_supstr_of=letters,min_length=NUM_LETTERS,is_alpha=True),
                    message = message
                )
                await word_input.run()
                word = word_input.responses[self.last_player]
                assert not word is None
                word = word.lower()
                word = "".join(word.split())#remove whitespace
                if self.is_word(word) and letters in word and len(word) > NUM_LETTERS:
                    definition = self.define(word)
                    definition_text = ""
                    if not definition is None:
                        definition_text = f"\n{self.definition_string(definition)}"
                    await self.basic_send(f"The word {word} is valid!{definition_text}")
                    self.last_player = player
                    return [player]
                elif not self.is_word(word):
                    await self.basic_send(f"I'm sorry, {self.format_players_md([self.last_player])}, '{word}' is not a valid word.")
                to_eliminate = self.last_player
                self.last_player = player
                return [to_eliminate]
                
                
