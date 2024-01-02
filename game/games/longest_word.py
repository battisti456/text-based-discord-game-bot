from game import PlayerId,MessageId
from game.game_bases import Dictionary_Base,Rounds_With_Points_Base
from game.game_interface import Game_Interface

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
        change_letters:MessageId = await self.basic_send(f"The current letters are '{self.current_letters}'.\n" + 
                                                   "*Respond here with the letters you want to change, if any*.\n" + 
                                                   f"You have {NUM_LETTERS_CAN_REFRESH} letter changes left.")
        choose_word:MessageId = await self.basic_send(f"*Respond here with your word when you have decided.*")

        amount_refreshed:list[int] = []
        async def change_letter_action(message:str,user_id:PlayerId):
            num_letters_refreshed_so_far = sum(amount for amount in amount_refreshed)
            if user_id == player and num_letters_refreshed_so_far < NUM_LETTERS_CAN_REFRESH:
                num_refreshed = 0
                list_letter = list(self.current_letters)
                for letter in message:
                    if letter in list_letter and num_refreshed < NUM_LETTERS_CAN_REFRESH - num_letters_refreshed_so_far:
                        num_refreshed += 1
                        list_letter.remove(letter)
                self.current_letters = "".join(list_letter) + self.random_balanced_letters(num_refreshed)
                amount_refreshed.append(num_refreshed)
                num_left = NUM_LETTERS_CAN_REFRESH-num_letters_refreshed_so_far-num_refreshed
                if num_left:
                    await self.basic_send(f"The current letters are '{self.current_letters}'.\n" + 
                                    "*Respond here with the letters you want to change, if any*.\n" + 
                                    f"You have {num_left} letter changes left.",
                                    message_id=change_letters)
                else:
                    await self.basic_send(f"The current letters are '{self.current_letters}'.\n" +
                                    "You have used all of your letter refreshes.",
                                    message_id=change_letters)
        word_holder:list[str] = []
        async def choose_word_action(message:str,user_id:PlayerId):
            if user_id == player:
                word = message.lower()
                warning:str = None
                if word in self.words_used:
                    warning = "was previously used in this game"
                elif not word.isalpha():
                    warning = "contains non-letter characters"
                else:
                    letter_list = list(self.current_letters)
                    for letter in word:
                        if letter in letter_list:
                            letter_list.remove(letter)
                        else:
                            warning = f"contained a letter '{letter}' that was either not in, or was in excess of the amount in '{self.current_letters}'."
                if warning is None:
                    word_holder.append(word)
                else:
                    await self.basic_send("*Respond here with your word when you have decided.*\n" + 
                                    f"Your attempt '{message}' was rejected because it {warning}.",
                                    message_id=choose_word)
        self.add_message_action(change_letters,change_letter_action)
        self.add_message_action(choose_word,choose_word_action)
        while word_holder == []:
            await self.wait(game.CHECK_TIME)
        self.remove_message_action(change_letters)
        self.remove_message_action(choose_word)
        total_refreshed = sum(amount for amount in amount_refreshed)
        await self.score(player,-total_refreshed)
        return word_holder[0]
    
    async def core_game(self):
        for player in self.players:
            word = await self.longest_word_question(player)
            if self.is_word(word):
                p= POINT_FUNCTION(word)
                await self.score(player,p)
                self.words_used.append(word)
                await self.basic_send(f"The word '{word}' is valid!")
            else:
                await self.basic_send(f"I'm sorry. Your guess of '{word}' is not in our dictionary.")
        

                
        

