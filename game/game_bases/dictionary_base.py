from game.game import Game
from game.game_interface import Game_Interface

import PyDictionary
import fogleman_TWL06_scrabble as scrabble
import wonderwords
import random
from typing import Literal, get_args

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


type PartOfSpeach = Literal['Noun','Verb','Adjective','Adverb']

type DefinitionDict = dict[PartOfSpeach,list[str]]
type DefinitionList = list[tuple[PartOfSpeach,str]]

def definition_dict_to_list(value:DefinitionDict) -> DefinitionList:
    to_return:DefinitionList = []
    for pos in value:
        for _def in value[pos]:
            to_return.append((pos,_def))
    return to_return
        
class Dictionary_Base(Game):
    def __init__(self,gh:Game_Interface):
        Game.__init__(self,gh)
        if not Dictionary_Base in self.initialized_bases:
            self.initialized_bases.append(Dictionary_Base)
            self.dictionary = PyDictionary.PyDictionary()
            self.ww_word = wonderwords.RandomWord()
            self.ww_sentence = wonderwords.RandomSentence()
    def is_word(self,word:str) -> bool:
        return scrabble.check(word)
    def define(self,word:str) -> DefinitionDict | None:
        return self.dictionary.meaning(word,True)
    def random_balanced_letters(self,num:int = 5) -> str:
        letter_list = random.choices(LETTERS,LETTER_WEIGHTS,k = num)
        return "".join(letter_list)
    def _definintion_string(self,defs_list:DefinitionList) -> str:
        formatted_strings:list[str] = []
        for _def in defs_list:
            close_paranthesis = ""
            if "(" in _def[1]:
                close_paranthesis = ")"
            formatted_strings.append(
                f"> {_def[0]}: *{_def[1]}{close_paranthesis}*"
            )
        return '\n'.join(formatted_strings)
            
    def definition_string(self,value:DefinitionList|DefinitionDict) -> str:
        if isinstance(value,list):
            return self._definintion_string(value)
        else:
            return self._definintion_string(definition_dict_to_list(value))
        
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
        
