from game import PlayerId,MessageId
from game.game_bases import Dictionary_Base,Rounds_With_Points_Base
from game.game_interface import Game_Interface
from game.message import Message, Alias_Message
from game.player_input import Player_Text_Input, run_inputs
from game.response_validator import text_validator_maker

NUM_LETTERS = 10
POINT_FUNCTION = lambda word: len(word)**2
NUMBER_OF_ROUNDS = 3
NUM_LETTERS_CAN_REFRESH:int = 5

class Longest_Word(Dictionary_Base,Rounds_With_Points_Base):
    def __init__(self,gi:Game_Interface):
        Dictionary_Base.__init__(self,gi)
        Rounds_With_Points_Base.__init__(self,gi)

        self.num_rounds = NUMBER_OF_ROUNDS
        self.words_used = []
        self.current_letters = self.random_balanced_letters(NUM_LETTERS)
    async def game_intro(self):
        await self.basic_send("# We are playing a game of create the longest word.\n" +
                  f"Each turn you will be given a set of {NUM_LETTERS} letters and the choice of whether or not to refresh them.\n" +
                  "If you do, you spend as many points as letters you refreshed.\n" +
                  "You can go into negative points.\n" +
                  "Then you must give the longest valid word that can be made from only those letters.\n" +
                  "You will get as many points as the word is long squared.\n" +
                  "Then the letters are passed on to the next player.")
    async def longest_word_question(self,player:PlayerId) -> str:
        num_letters_can_refresh = NUM_LETTERS_CAN_REFRESH
        change_letter_message = Alias_Message(
            Message(),
            lambda content: f"**Which letters in '{self.current_letters}' would you like to swap, if any? You can swap {num_letters_can_refresh} letters.**")
        choose_word_message = Alias_Message(
            Message(),
            lambda content: f"**What word will you spell with '{self.current_letters}'?**")
        change_letter_input = Player_Text_Input(
            "change letter",
            self.gi,
            self.sender,
            [player],
            lambda x,y: text_validator_maker(is_stricly_composed_of=self.current_letters,max_length=num_letters_can_refresh,check_lower_case=True)(x,y),
            message=change_letter_message
        )
        choose_word_input = Player_Text_Input(
            "choose word",
            self.gi,
            self.sender,
            [player],
            lambda x,y: text_validator_maker(is_stricly_composed_of=self.current_letters,check_lower_case=True)(x,y),
            message=choose_word_message
        )
        chosen_word:None|str = None
        while chosen_word is None:
            await self.sender(change_letter_message)
            await self.sender(choose_word_message)
            if num_letters_can_refresh:
                change_letter_input.reset()
                choose_word_input.reset()
                await run_inputs([change_letter_input,choose_word_input],[{change_letter_input},{choose_word_input}])
            else:
                choose_word_input.reset()
                await choose_word_input.run()
            if choose_word_input.has_recieved_all_responses():
                chosen_word = choose_word_input.responses[player]
            else:
                change_letters = change_letter_input.responses[player] 
                if not change_letters is None:
                    list_letters = list(self.current_letters)
                    for letter in change_letters:
                        list_letters.remove(letter)
                    list_letters += self.random_balanced_letters(NUM_LETTERS-len(list_letters))
                    self.current_letters = "".join(list_letters)
                    num_letters_can_refresh -= len(change_letters)
        return chosen_word
    
    async def core_game(self):
        for player in self.unkicked_players:
            word = await self.longest_word_question(player)
            if self.is_word(word):
                p= POINT_FUNCTION(word)
                await self.score([player],p)
                self.words_used.append(word)
                await self.basic_send(f"The word '{word}' is valid!")
            else:
                await self.basic_send(f"I'm sorry. Your guess of '{word}' is not in our dictionary.")
        

                
        

