from typing import Any, override, Annotated

from config_system_battisti456.config_item import Integer
from config import Config
from game.components.game_interface import Game_Interface
from game.components.input_ import Status_Display
from game.components.input_.response_validator import text_validator_maker
from game.components.participant import Player
from game.components.send import Address, sendables
from game.game_bases import Game_Word_Base, Rounds_With_Points_Base

class config(Config):
    num_letters:Annotated[int,Integer(level=1,min_value=1)] = 10
    num_rounds:Annotated[int,Integer(level=1,min_value=1)] = 3
    num_letters_can_refresh:Annotated[int,Integer(level=1,min_value=0)] = 5

def POINT_FUNCTION(word):
    return len(word)**2

class Longest_Word(Game_Word_Base,Rounds_With_Points_Base):
    def __init__(self,gi:Game_Interface):
        Game_Word_Base.__init__(self,gi)
        Rounds_With_Points_Base.__init__(self,gi)

        self.num_rounds = config.num_rounds
        self.words_used = []
        self.current_letters = self.random_balanced_letters(config.num_letters)
    @override
    async def game_intro(self):
        await self.say(
            "# We are playing a game of create the longest word.\n" +
            f"Each turn you will be given a set of {config.num_letters} letters and the choice of whether or not to refresh them.\n" +
            "If you do, you spend as many points as letters you refreshed.\n" +
            "You can go into negative points.\n" +
            "Then you must give the longest valid word that can be made from only those letters.\n" +
            "You will get as many points as the word is long squared.\n" +
            "Then the letters are passed on to the next player.")
    async def longest_word_question(self,player:Player) -> str:
        num_letters_can_refresh = config.num_letters_can_refresh
        change_letter_address:Address = await self.sender.generate_address()
        choose_word_address:Address = await self.sender.generate_address()

        change_letter_input = self.im.text(
            identifier="change letter",
            participants=[player],
            response_validator=lambda x,y: text_validator_maker(is_strictly_composed_of=self.current_letters,max_length=num_letters_can_refresh,check_lower_case=True)(x,y),
            interaction_filter=change_letter_address.get_filter()
        )
        choose_word_input = self.im.text(
            identifier="choose word",
            participants=[player],
            response_validator=lambda x,y: text_validator_maker(is_strictly_composed_of=self.current_letters,check_lower_case=True)(x,y),
            interaction_filter=choose_word_address.get_filter()
        )
        class _(Status_Display[Any,Any,Any]):
            @override
            async def display(*_):
                await self.sender(sendables.Text_With_Text_Field(
                    text = f"**Which letters in '{self.current_letters}' would you like to swap, if any? You can swap {num_letters_can_refresh} letters.**"
                ),change_letter_address)
                await self.sender(sendables.Text_With_Text_Field(
                    text = f"**What word will you spell with '{self.current_letters}'?**"
                ),choose_word_address)
        status_display = (_(change_letter_address),)
        change_letter_input.on_updates = status_display
        choose_word_input.on_updates = status_display
        
        chosen_word:None|str = None
        while chosen_word is None:
            await status_display[0].display()
            if num_letters_can_refresh:
                change_letter_input.reset()
                choose_word_input.reset()
                await self.im.run(change_letter_input,choose_word_input,completion_sets=[{change_letter_input},{choose_word_input}])
            else:
                choose_word_input.reset()
                await choose_word_input.run()
            if choose_word_input.responses[player] is None:
                if not num_letters_can_refresh or change_letter_input.responses[player] is None:
                    await self.kick_players([player],reason='timeout')
                    return ""
            if choose_word_input.is_done():
                chosen_word = choose_word_input.responses[player].text#type:ignore
            else:
                change_letters = change_letter_input.responses[player].text#type:ignore
                if change_letters is not None:
                    list_letters = list(self.current_letters)
                    for letter in change_letters:
                        list_letters.remove(letter)
                    list_letters += self.random_balanced_letters(config.num_letters-len(list_letters))
                    self.current_letters = "".join(list_letters)
                    num_letters_can_refresh -= len(change_letters)
        return chosen_word
    @override
    async def core_round(self):
        for player in self.unkicked_players:
            word = await self.longest_word_question(player)
            if player in self.kicked_players:
                continue
            if self.is_valid_word(word):
                p= POINT_FUNCTION(word)
                await self.score([player],p)
                self.words_used.append(word)
                await self.say(f"The word '{word}' is valid!")
            else:
                await self.say(f"I'm sorry. Your guess of '{word}' is not in our dictionary.")