from typing import override

from config.games_config import games_config
from game.components.game_interface import Game_Interface
from game.components.player_input import Player_Text_Input, run_inputs
from game.components.response_validator import text_validator_maker
from game.game_bases import Game_Word_Base, Rounds_With_Points_Base
from utils.types import PlayerId
from game.components.send import sendables

CONFIG = games_config['longest_word']

NUM_LETTERS = CONFIG['num_letters']
def POINT_FUNCTION(word):
    return len(word)**2
NUMBER_OF_ROUNDS = CONFIG['number_of_rounds']
NUM_LETTERS_CAN_REFRESH:int = CONFIG['num_letters_can_refresh']

class Longest_Word(Game_Word_Base,Rounds_With_Points_Base):
    def __init__(self,gi:Game_Interface):
        Game_Word_Base.__init__(self,gi)
        Rounds_With_Points_Base.__init__(self,gi)

        self.num_rounds = NUMBER_OF_ROUNDS
        self.words_used = []
        self.current_letters = self.random_balanced_letters(NUM_LETTERS)
    @override
    async def game_intro(self):
        await self.say(
            "# We are playing a game of create the longest word.\n" +
            f"Each turn you will be given a set of {NUM_LETTERS} letters and the choice of whether or not to refresh them.\n" +
            "If you do, you spend as many points as letters you refreshed.\n" +
            "You can go into negative points.\n" +
            "Then you must give the longest valid word that can be made from only those letters.\n" +
            "You will get as many points as the word is long squared.\n" +
            "Then the letters are passed on to the next player.")
    async def longest_word_question(self,player:PlayerId) -> str:
        num_letters_can_refresh = NUM_LETTERS_CAN_REFRESH
        change_letter_address = await self.sender.generate_address()
        choose_word_address = await self.sender.generate_address()

        change_letter_input = Player_Text_Input(
            "change letter",
            self.gi,
            self.sender,
            [player],
            response_validator=lambda x,y: text_validator_maker(is_strictly_composed_of=self.current_letters,max_length=num_letters_can_refresh,check_lower_case=True)(x,y),
            question_address=change_letter_address
        )
        choose_word_input = Player_Text_Input(
            "choose word",
            self.gi,
            self.sender,
            [player],
            response_validator=lambda x,y: text_validator_maker(is_strictly_composed_of=self.current_letters,check_lower_case=True)(x,y),
            question_address=choose_word_address
        )
        @change_letter_input.on_update
        @choose_word_input.on_update
        async def update_display():
            await self.sender(sendables.Text_With_Text_Field(
                text = f"**Which letters in '{self.current_letters}' would you like to swap, if any? You can swap {num_letters_can_refresh} letters.**"
            ),change_letter_address)
            await self.sender(sendables.Text_With_Text_Field(
                text = f"**What word will you spell with '{self.current_letters}'?**"
            ),choose_word_address)
        
        chosen_word:None|str = None
        while chosen_word is None:
            await update_display()#type:ignore
            if num_letters_can_refresh:
                change_letter_input.reset()
                choose_word_input.reset()
                await run_inputs([change_letter_input,choose_word_input],[{change_letter_input},{choose_word_input}])
            else:
                choose_word_input.reset()
                await choose_word_input.run()
            if choose_word_input.responses[player] is None:
                if not num_letters_can_refresh or change_letter_input.responses[player] is None:
                    await self.kick_players([player],reason='timeout')
                    return ""
            if choose_word_input.has_received_all_responses():
                chosen_word = choose_word_input.responses[player]
            else:
                change_letters = change_letter_input.responses[player] 
                if change_letters is not None:
                    list_letters = list(self.current_letters)
                    for letter in change_letters:
                        list_letters.remove(letter)
                    list_letters += self.random_balanced_letters(NUM_LETTERS-len(list_letters))
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