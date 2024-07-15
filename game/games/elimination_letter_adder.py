#NEEDS TO BE TESTED
import random
from typing import override

from config.games_config import games_config
from game.components.game_interface import Game_Interface
from game.components.player_input import (
    Player_Single_Selection_Input,
    Player_Text_Input,
    run_inputs,
)
from game.components.send.sendable.sendables import Text_With_Options_And_Text_Field, Text_With_Text_Field
from game.components.response_validator import text_validator_maker
from game.components.send.old_message import Old_Message
from game.game_bases.elimination_base import Elimination_Base
from game.game_bases.game_word_base import Game_Word_Base
from game.components.send.option import make_options, NO_YES_OPTIONS
from utils.emoji_groups import LEFT_RIGHT_EMOJI
from utils.types import PlayerId

NUM_LETTERS = games_config['elimination_letter_adder']['num_letters']
START_LETTERS = games_config['elimination_letter_adder']['start_letters']

class Elimination_Letter_Adder(Elimination_Base,Game_Word_Base):
    def __init__(self,gi:Game_Interface):
        Elimination_Base.__init__(self,gi)
        Game_Word_Base.__init__(self,gi)
        self.last_player:PlayerId = self.unkicked_players[0]
    @override
    async def game_intro(self):
        await self.say(
            "# We are playing a game of word creation!\n" +
            "In this game you take turns adding letters to the combined letters, choosing to put them on the left or right side.\n" +
            f"Once we have more than {NUM_LETTERS}, if you add a letter that makes it spell a word, you lose!\n" +
            "But, beware! If the person after you challenges your word you must provide a word " + 
            "that could still be spelled with the letters, or else you are eliminated.\n" +
            "If the challenge was made in haste, however, the challenger is eliminated instead.\n" +
            f"To start us off in a round, I will generate {START_LETTERS} letters which are definitely a part of a word."
        )
    @override
    async def core_round(self):
        num_letters_in_starting_word = START_LETTERS + random.randint(1,len(self.unkicked_players))
        starting_word = self.random_valid_word(num_letters_in_starting_word)
        offset = random.randint(0,num_letters_in_starting_word-START_LETTERS-1)
        letters = starting_word[offset:offset+START_LETTERS]
        first_turn = True
        while True:
            #determine whose turn it is
            main_index = self.all_players.index(self.last_player)
            for i in range(1,len(self.all_players)):
                player = self.all_players[(main_index+i)%len(self.unkicked_players)]
                if player in self.unkicked_players:
                    break
            await self.say(f"The letters are '{letters}'.")
            will_challenge_message = Old_Message(
                text=f"Will you challenge {self.sender.format_players_md([self.last_player])}?",
                with_options=NO_YES_OPTIONS
            )
            if not first_turn:
                will_challenge_address = await self.sender(will_challenge_message)
                challenge_input = Player_Single_Selection_Input(
                    "choice to challenge",
                    self.gi,
                    self.sender,
                    [player],
                    question_address=will_challenge_address,
                    response_validator=lambda player, value: (bool(value),None)
            )
            letter_sendable = Text_With_Options_And_Text_Field(
                text = "Which side would you like to put your letter on, and which letter would you like to add?",
                with_options=make_options(['left','right'],LEFT_RIGHT_EMOJI),
                hint_text="Which letter would you like?"
            )
            letter_address = await self.sender(letter_sendable)
            left_right_input = Player_Single_Selection_Input(
                "choice of left or right",
                self.gi,
                self.sender,
                [player],
                question_address=letter_address
            )
            letter_input = Player_Text_Input(
                "choice of letter",
                self.gi,
                self.sender,
                [player],
                question_address=letter_address,
                response_validator=text_validator_maker(max_length=1,min_length=1,is_alpha=True)
            )
            if first_turn:
                await run_inputs(
                    inputs = [left_right_input,letter_input],
                )
                await self.kick_none_response(left_right_input.responses)
                await self.kick_none_response(letter_input.responses)
            else:
                await run_inputs(
                    inputs = [challenge_input,left_right_input,letter_input],
                    completion_sets= [{challenge_input},{left_right_input,letter_input}],
                )
                if not challenge_input.responses[player]:
                    await self.kick_none_response(left_right_input.responses)
                    await self.kick_none_response(letter_input.responses)
            if player in self.kicked_players or self.last_player in self.kicked_players:
                #if one of the two relevant players has been kicked, move to next round
                self.last_player = player
                return
            if first_turn or not challenge_input.responses[player]:#add letter
                first_turn = False
                letter = letter_input.responses[player]
                assert letter is not None
                letter = letter.lower()
                if left_right_input.responses[player]:#1 is right
                    letters = letters + letter
                else:
                    letters = letter + letters
                if len(letters) > NUM_LETTERS and self.is_valid_word(letters):
                    definition = self.define(letters)
                    def_text = ""
                    if definition is not None:
                        def_text = f"\nHere are some definitions:\n{self.definition_string(definition)}"
                    await self.say(
                        f"{self.format_players_md([player])} has spelled the word {letters}.{def_text}")
                    self.last_player = player
                    await self.eliminate([player])
                    return
                else:
                    self.last_player = player
                    continue 
            else:#challenge
                message = Text_With_Text_Field(
                    text = f"{self.format_players_md([player])} has chosen to challenge {self.format_players_md([self.last_player])} on the letters '{letters}'. \n" +
                    "What word do you think you could have spelled?")
                address = await self.sender(message)
                word_input = Player_Text_Input(
                    "word",
                    self.gi,
                    self.sender,
                    [self.last_player],
                    response_validator=text_validator_maker(is_supstr_of=letters,min_length=NUM_LETTERS,is_alpha=True),
                    question_address=address
                )
                await word_input.run()
                await self.kick_none_response(word_input.responses)
                if self.last_player in self.kicked_players:
                    self.last_player = player
                    return
                word = word_input.responses[self.last_player]
                assert word is not None
                word = word.lower()
                word = "".join(word.split())#remove whitespace
                if self.is_valid_word(word) and letters in word and len(word) > NUM_LETTERS:
                    definition = self.define(word)
                    definition_text = ""
                    if definition is not None:
                        definition_text = f"\n{self.definition_string(definition)}"
                    await self.say(f"The word {word} is valid!{definition_text}")
                    self.last_player = player
                    await self.eliminate([player])
                    return
                elif not self.is_valid_word(word):
                    await self.say(f"I'm sorry, {self.format_players_md([self.last_player])}, '{word}' is not a valid word.")
                    await self.eliminate([self.last_player])
                    self.last_player = player
                    return
                
                
