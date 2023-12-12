import game

import PyDictionary
import fogleman_TWL06_scrabble as scrabble
import random
from typing import Literal

LETTER_FREQUENCY = {
    "a" : 9,
    "b" : 2,
    "c" : 2,
    "d" : 4,
    "e" : 12,
    "f" : 2,
    "g" : 3,
    "h" : 2,
    "i" : 9,
    "j" : 1,
    "k" : 1,
    "l" : 4,
    "m" : 2,
    "n" : 6,
    "o" : 8,
    "p" : 2,
    "q" : 1,
    "r" : 6,
    "s" : 4,
    "t" : 6,
    "u" : 4,
    "v" : 2,
    "w" : 2,
    "x" : 1,
    "y" : 2,
    "z" : 1
}
LETTERS:list[str] = list(letter for letter in LETTER_FREQUENCY)
LETTER_WEIGHTS:list[int|float] = list(LETTER_FREQUENCY[letter] for letter in LETTERS)

WORD_LIST_LEN_CAP = 100

partofspeach = Literal['Noun','Verb','Adjective','Adverb']
definitiondict = dict[partofspeach,list[str]]


class Dictionary_Base(game.Game):
    def __init__(self,gh:game.GH):
        game.Game.__init__(self,gh)
        self.dictionary = PyDictionary.PyDictionary()
    def is_word(self,word:str) -> bool:
        return scrabble.check(word)
    def define(self,word:str) -> definitiondict:
        return self.dictionary.meaning(word,True)
    def random_balanced_letters(self,num:int = 5) -> str:
        letter_list = random.choices(LETTERS,LETTER_WEIGHTS,k = num)
        return "".join(letter_list)
    def definition_string(self,*args:list[tuple[partofspeach,str]|list[tuple[partofspeach,str]]|definitiondict]|list[partofspeach,str]) -> str:
        if len(args) == 2 and all(isinstance(item,str) for item in def_):
            args = [args]
        defs:list[tuple[partofspeach,str]] = []
        for def_ in args:
            if len(def_) == 2 and all(isinstance(item,str) for item in def_):
                defs.append(def_)
            elif isinstance(def_,list):
                defs += def_
            elif isinstance(def_,dict):
                for part in def_:
                    defs.append(part,def_[part])
        for def_ in defs:
            if '(' in def_[1] and not ')' in def_[1]:
                def_[1] += ")"
        return "\n".join(f"> {def_[0].lower()}: **{def_[1]}**" for def_ in defs)
        
    def random_word(self,length:int = 5) -> str:
        letters = self.random_balanced_letters(length*2)
        words = scrabble.anagram(letters)
        valid_words:list[str] = []
        for word in words:
            if len(word) == length:
                valid_words.append(word)
                if len(valid_words) == WORD_LIST_LEN_CAP:
                    break
        if valid_words:
            return random.choice(valid_words)
        else:
            return self.random_word(length)
        
