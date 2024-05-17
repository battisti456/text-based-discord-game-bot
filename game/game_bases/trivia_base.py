from game import PlayerId, PlayerDict
from game.game import Game
from game.components.game_interface import Game_Interface
import pytrivia

from typing import TypedDict, Optional, Iterable

import random

class TriviaDict(TypedDict):
    question: str
    correct_answer: str
    incorrect_answers: list[str]
    type: str
    difficulty: str
    category: str

class Trivia_Base(Game):
    def __init__(self,gi:Game_Interface):
        Game.__init__(self,gi)
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
    async def get_trivia(
            self,category:Optional[pytrivia.Category|str] = None,
            difficulty:Optional[pytrivia.Diffculty|str] = None,
            type_:Optional[pytrivia.Type|str] = None) -> TriviaDict:
        if isinstance(category,str):
            category = self.get_category(category)
        if isinstance(difficulty,str):
            difficulty = self.get_difficulty(difficulty)
        if isinstance(type_,str):
            type_= self.get_type(type_)
        kwargs = {}
        if not category is None:
            kwargs['category'] = category
        if not difficulty is None:
            kwargs['diffculty'] = difficulty
        if not type_ is None:
            kwargs['type_'] = type_
        raw = self.trivia_client.request(1,**kwargs)
        while not 'results' in raw:#might time out if wait long enough?
            self.trivia_client = pytrivia.Trivia(True)
            raw = self.trivia_client.request(1,**kwargs)
        return raw['results'][0]
    async def basic_ask_trivia(
            self,players:Iterable[PlayerId],
            category:Optional[pytrivia.Category] = None,
            difficulty:Optional[pytrivia.Diffculty] = None,
            type_:Optional[pytrivia.Type] = None) -> dict[PlayerId,bool]:
        question = await self.get_trivia(category,difficulty,type_)
        options:list[str] = []
        if question['type'] == 'multiple':
            options += question['incorrect_answers']
            options.append(question['correct_answer'])
            random.shuffle(options)
            choices:PlayerDict[int] = await self.basic_multiple_choice(question['question'],options,players)
        else:#boolean
            options = ['False','True']
            choices:PlayerDict[int] = await self.basic_no_yes(question['question'],players)
        await self.basic_send(f"The correct answer was '{question['correct_answer']}'.")
        correct_index = options.index(question['correct_answer'])
        player_correct:dict[PlayerId,bool] = {}
        for player in set(players) & set(self.unkicked_players):
            player_correct[player] = choices[player] == correct_index
        return player_correct
