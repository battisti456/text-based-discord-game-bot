import game
from game.game_bases.elimination_base import Elimination_Base
from game.game_bases.dictionary_base import Dictionary_Base

from typing import Iterable

NUM_LETTERS = 4
LEFT_RIGHT_CHALLENGE_EMOJI = ['⬅️','➡️','📖']

class Elimination_Letter_Adder(Elimination_Base,Dictionary_Base):
    def __init__(self,gh:game.GH):
        Elimination_Base.__init__(self,gh)
        Dictionary_Base.__init__(self,gh)

        self.last_player:int = self.players[0]
    async def game_intro(self):
        await self.send(
            f"""# We are playing a game of word creation!
            In this game you take turns adding letters to the combined letters, choosing to put them on the left or right side.
            Once we have more than {NUM_LETTERS}, if you add a letter that makes it spell a word, you lose!
            But, beware! If the person after you challenges your word you must provide a word that could still be spelled with the letters, or else you are eliminated.
            If the challenge was made in haste, however, the challenger is eliminated instead."""
        )
    async def game_outro(self,order:Iterable[int]):
        pass
    async def core_game(self,remaining_players:Iterable[int])->Iterable[int]|int:
        letters = ""
        while True:
            #determine whose turn it is
            player = None
            main_index = self.players.index(self.last_player)
            for i in range(1,len(self.players)):
                player = self.players[(main_index+i)%len(self.players)]
                if player in remaining_players:
                    break
            #
            if not letters == "":
                message = f"{self.mention(player)}, what would you like to do?"
                choices = ['add to left','add to right']
                if len(letters) > 1:
                    choices.append('challenge')
                choice = await self.multiple_choice(message,choices,player,LEFT_RIGHT_CHALLENGE_EMOJI)
            else:
                await self.send("Let's start off our word!")
                choice = 0
            if choice in [0,1]:#add letter
                letter:str = await self.text_response(f"{self.mention(player)}, which letter would you like?",player)
                while len(letter) > 1 or not letter.isalpha():
                    letter:str = await self.text_response(f"{self.mention(player)}, I am sorry, '{letter}' is not a valid response.",player)
                letter = letter.lower()
                if choice:#1 is right
                    letters = letters + letter
                else:
                    letters = letter + letters
                if len(letters) > NUM_LETTERS and self.is_word(letters):
                    await self.send(
                        f"""{self.mention(player)} has spelled the word {letters}.
                        Here are some definitions:
                        {self.definition_string(self.define(letters))}""")
                    self.last_player = player
                    return player
                else:
                    self.last_player = player
                    await self.send(f"Our letters are now '{letters}'.")
                    continue#unnessasary but helps with readability for me
            else:#challenge
                await self.send(f"{self.mention(player)} has chosen to challenge {self.mention(self.last_player)} on the letters '{letters}'")
                word = await self.text_response(f"{self.mention(self.last_player)}, What word do you think you could have spelled with '{letters}'?",self.last_player)
                word = word.lower()
                word = "".join(word.split())#remove whitespace
                if self.is_word(word) and letters in word and len(word) > NUM_LETTERS:
                    await self.send(f"The word {word} is valid!\n{self.define(word)}")
                    self.last_player = player
                    return player
                elif not self.is_word(word):
                    await self.send(f"I'm sorry, {self.mention(self.last_player)}, '{word}' is not a valid word.")
                elif not letters in word:
                    await self.send(f"I'm sorry, '{word}' does not contain '{letters}'.")
                elif not len(word) <= NUM_LETTERS:
                    await self.send(f"I'm sorry, '{word}' does not reach our length requirement of {NUM_LETTERS}.")
                to_eliminate = self.last_player
                self.last_player = player
                return to_eliminate
                
                
