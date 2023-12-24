import game
from game import PlayerId
import pytrivia

from typing import Iterable, TypedDict

import random

class TriviaDict(TypedDict):
    question: str
    correct_answer: str
    incorrect_answers: list[str]
    type: str
    difficulty: str
    category: str


class Trivia_Base(game.Game):
    def __init__(self,gh:game.GH):
        game.Game.__init__(self,gh)
        if not Trivia_Base in self.initialized_bases:
            self.initialized_bases.append(Trivia_Base)
            self.trivia_client = pytrivia.Trivia(True)
            self.difficulty = pytrivia.Diffculty
            self.category = pytrivia.Category
            self.type_ = pytrivia.Type
    def get_difficulty(self,text:str):
        text = text.capitalize()
        if hasattr(self.difficulty,text):
            return eval(f"self.difficulty.{text}")
        else:
            raise Exception(f"There is no trivia difficulty '{text}'.")
    def get_category(self,text:str):
        text = text.capitalize()
        if hasattr(self.category,text):
            return eval(f"self.category.{text}")
        else:
            raise Exception(f"There is no trivia category '{text}'.")
    def get_type(self,text:str):
        text = text.capitalize()
        if hasattr(self.type_,text):
            return eval(f"self.type_.{text}")
        else:
            raise Exception(f"There is no trivia type '{text}'.")
    async def get_trivia(self,category:pytrivia.Category|str = None,difficulty:pytrivia.Diffculty|str = None,type_:pytrivia.Type|str = None) -> TriviaDict:
        if isinstance(category,str):
            category = self.get_category(category)
        if isinstance(difficulty,str):
            difficulty = self.get_difficulty(difficulty)
        if isinstance(type_,str):
            type_= self.get_type(type_)
        raw = self.trivia_client.request(1,category,difficulty,type_)
        while not 'results' in raw:#might time out if wait long enough?
            self.trivia_client = pytrivia.Trivia(True)
            raw = self.trivia_client.request(1,category,difficulty,type_)
        return raw['results'][0]
    async def ask_trivia(self,players:list[PlayerId],category:pytrivia.Category = None,difficulty:pytrivia.Diffculty = None,type_:pytrivia.Type = None) -> dict[PlayerId,bool]:
        question = await self.get_trivia(category,difficulty,type_)
        options:list[str] = []
        if question['type'] == 'multiple':
            options += question['incorrect_answers']
            options.append(question['correct_answer'])
            random.shuffle(options)
            choices:list[PlayerId,int] = await self.multiple_choice(question['question'],options,players)
        else:#boolean
            options = ['False','True']
            choices:list[PlayerId,int] = await self.no_yes(question['question'],players)
        await self.send(f"The correct answer was '{question['correct_answer']}'.")
        correct_index = options.index(question['correct_answer'])
        player_correct:dict[PlayerId,bool] = {}
        for player in players:
            player_correct[player] = choices[player] == correct_index
        return player_correct
