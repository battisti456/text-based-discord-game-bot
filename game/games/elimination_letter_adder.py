#VERY BUGGY
import random
from typing import override, Literal

from config.games_config import games_config
from game.components.send.address import Address
from game.components.game_interface import Game_Interface
from game.components.input_ import Input
from game.components.input_.response_validator import text_validator_maker
from game.components.participant import Player, mention_participants
from game.components.send.sendable.sendables import (
    Text_With_Text_Field,
)
from game.game_bases.elimination_base import Elimination_Base
from game.game_bases.game_word_base import Game_Word_Base
from utils.grammar.types import Lower_Case_Letter, LOWER_CASE_LETTERS
from utils.emoji_groups import LETTER_KEYCAP_EMOJI, FIGHT_SURRENDER_EMOJI, LEFT_RIGHT_EMOJI
from smart_text import TextLike
from game.components.send.interaction import  Interaction, Select_Options, Option
from game.components.send import make_sendable, Sendable

NUM_LETTERS = games_config['elimination_letter_adder']['num_letters']
START_LETTERS = games_config['elimination_letter_adder']['start_letters']

type Letter_Add_Input_Type = None | tuple[bool,Lower_Case_Letter]
"None for no answer or challenge if available, tuple[0] left if true, tuple[1] the letter choice"

class Letter_Add_Input(Input[Letter_Add_Input_Type, Literal['Multi_Input'], Player]):
    def __init__(
            self,
            gi:Game_Interface,
            player:Player,
            letters:str,
            can_challenge:bool
            ):
        self._player= player
        self._letters = letters
        self._can_challenge = can_challenge
        self._address0:Address
        self._address1:Address
        self._in_would_you_like_to_challenge_phase = self._can_challenge
        self._player_is_done = False
        self._letter:Lower_Case_Letter|None = None
        self._left:bool|None = None
        super().__init__(
            gi=gi,
            participants=(player,),
            identifier=f"{player.user_name}'s choice on '{letters}'."
        )
    def is_done(self) -> bool:
        return self._player_is_done or (self._letter is not None and self._left is not None)
    def current_letters_text(self) -> TextLike:
        return f"The letters are currently '{self._letters}'.\n"
    def challenge_text(self) -> Sendable:
        return make_sendable(
            text = f"{self.current_letters_text()}Would you like to challenge the previous player to prove spelling a word is possible?",
            with_options=(
                Option(
                    text = 'challenge',
                    emoji=FIGHT_SURRENDER_EMOJI[0],
                    long_text='challenge the letters'
                ),
                Option(
                    text = 'letter',
                    emoji=FIGHT_SURRENDER_EMOJI[1],
                    long_text='add a letter'
                )
            ),
            min_selectable=1,
            max_selectable=1
        )
    def side(self) -> Sendable:
        return make_sendable(
            text = (f"{self.current_letters_text()}Choose which letter you would like to add, and the side to add it to." +
                ("You may still select to challenge." 
                if self._can_challenge else "")
                ),
            with_options=(
                Option(
                    text = 'left',
                    emoji = LEFT_RIGHT_EMOJI[0],
                    long_text='place the letter on the left side of the letter collection'
                ),
                Option(
                    text='right',
                    emoji= LEFT_RIGHT_EMOJI[1],
                    long_text='place the letter on the right side of the letter collection'
                )
            )+((
                Option(
                    text='challenge',
                    emoji= FIGHT_SURRENDER_EMOJI[0],
                    long_text='nevermind, I do want to challenge this'
                ),
            ) if self._can_challenge else ()) 
        )
    def letter(self) -> Sendable:
        return make_sendable(
            with_options=tuple(
                Option(
                    text= LOWER_CASE_LETTERS[i],
                    emoji = LETTER_KEYCAP_EMOJI[i],
                    long_text=f"the letter {LOWER_CASE_LETTERS[i]}"
                )
                for i in range(len(LOWER_CASE_LETTERS))
            )
        )
    async def on_interaction(self,interaction:Interaction):
        if self._in_would_you_like_to_challenge_phase:
            if interaction.at_address != self._address0:
                return
            if isinstance(interaction.content,Select_Options):
                if interaction.content.indices[0] == 0:#challenge
                    self._player_is_done = True
                    await self.update_on_updates()
                else:
                    self._in_would_you_like_to_challenge_phase = False
                    await self.sender(self.side(),self._address0)
                    self._address1 = await self.sender(self.letter())
                    await self.update_on_updates()
        else:
            if not isinstance(interaction.content,Select_Options):
                return
            if interaction.at_address == self._address0:
                match (interaction.content.indices[0]):
                    case 0:#left
                        self._left = True
                    case 1:#right
                        self._left = False
                    case 2:#challenge
                        self._player_is_done = True
                await self.update_on_updates()
            elif interaction.at_address == self._address1:
                self._letter = LOWER_CASE_LETTERS[interaction.content.indices[0]]
                await self.update_on_updates()
            else:
                return
    async def setup(self):
        await super().setup()
        self._address0 = await self.sender(self.challenge_text() if self._can_challenge else self.side())
        if not self._can_challenge:
            self._address1 = await self.sender(self.letter())
        self.gi.watch(owner = self)(self.on_interaction)
    async def unsetup(self):
        await super().unsetup()
        self.gi.purge_actions(self)
        if self._letter is not None and self._left is not None:
            self.responses[self._player] = (self._left,self._letter)
        else:
            self.responses[self._player] = None

class Elimination_Letter_Adder(Elimination_Base,Game_Word_Base):
    def __init__(self,gi:Game_Interface):
        Elimination_Base.__init__(self,gi)
        Game_Word_Base.__init__(self,gi)
        self.last_player:Player = self.unkicked_players[0]
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
    async def core_round(self): # type: ignore
        num_letters_in_starting_word = START_LETTERS + random.randint(1,len(self.unkicked_players))
        starting_word = self.random_valid_word(num_letters_in_starting_word)
        offset = random.randint(0,num_letters_in_starting_word-START_LETTERS-1)
        letters = starting_word[offset:offset+START_LETTERS]
        first_turn = True
        while True:
            #determine whose turn it is
            player:Player|None = None
            main_index = self.all_players.index(self.last_player)
            for i in range(1,len(self.all_players)):
                player = self.all_players[(main_index+i)%len(self.unkicked_players)]
                if player in self.unkicked_players:
                    break
            assert player is not None
            input = Letter_Add_Input(
                gi = self.gi,
                player = player,
                letters = letters,
                can_challenge= not first_turn
            )
            response = input.responses[player]
            if response is None and first_turn:
                await self.kick_players([player],reason='timeout')
                self.last_player = player
                return
            elif response is not None:
                first_turn = False
                letter = response[1]
                if response[0]:#left
                    letters = letter + letters
                else:#right
                    letters = letters + letter
                if len(letters) > NUM_LETTERS and self.is_valid_word(letters):
                    definition = self.define(letters)
                    def_text = ""
                    if definition is not None:
                        def_text = f"\nHere are some definitions:\n{self.definition_string(definition)}"
                    await self.say(
                        f"{mention_participants([player])} has spelled the word {letters}.{def_text}")
                    self.last_player = player
                    await self.eliminate([player])
                    return
                else:
                    self.last_player = player
                    continue 
            else:#challenge
                message = Text_With_Text_Field(
                    text = f"{mention_participants([player])} has chosen to challenge {mention_participants([self.last_player])} on the letters '{letters}'. \n" +
                    "What word do you think you could have spelled?")
                address = await self.sender(message)
                word_input = await self.basic_text_response(
                    content=address,
                    who_chooses=[self.last_player],
                    response_validator=text_validator_maker(is_supstr_of=letters,min_length=NUM_LETTERS,is_alpha=True),
                )
                if self.last_player in self.kicked_players:
                    self.last_player = player
                    return
                word = word_input[self.last_player]
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
                    await self.say(f"I'm sorry, {mention_participants([self.last_player])}, '{word}' is not a valid word.")
                    await self.eliminate([self.last_player])
                    self.last_player = player
                    return
                
                
