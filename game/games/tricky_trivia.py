import game
from game import userid
from game.game_bases import Trivia_Base, Secret_Message_Base, Rounds_With_Points_Base
from game.game_bases.trivia_base import TriviaDict
import asyncio
import random

POINTS_FOOL = 1
POINTS_GUESS = 3
NUM_QUESTIONS = 3

class Tricky_Trivia(Secret_Message_Base,Trivia_Base,Rounds_With_Points_Base):
    def __init__(self,gh:game.GH):
        Secret_Message_Base.__init__(self,gh)
        Trivia_Base.__init__(self,gh)
        Rounds_With_Points_Base.__init__(self,gh)
    async def game_intro(self):
        await self.send(
            f"# Today we are playing a game of tricky trivia!\n" +
            "In this game you will be presented with trivia questions and each player will secretly craft their own possiple answer.\n" +
            "Then, the trivia question will be asked at large.\n" +
            f"You get {POINTS_FOOL} point for every person you fool, and {POINTS_GUESS} for getting it right yourself.\n" +
            f"We will do this for {NUM_QUESTIONS} questions(s).\n" +
            "If you provide the real answer, you will get as many points as people who guessed it, excluding yourself.\n" +
            "The highest points at the end wins!\n" +
            "**WARNING: Sometimes the trivia is phrased in such a way that you can provide an alternative correct answer. Please provide an incorrect answer!**"
        )
    async def core_game(self):
        trivia_dict:TriviaDict = await self.get_trivia(type_ = self.type_.Multiple_Choice)
        while trivia_dict['question'][0:5] == "Which" or "hich of these" in trivia_dict['question']:#hopefully prevent some bad qs
            trivia_dict = await self.get_trivia(type_ = self.type_.Multiple_Choice)
        question_text = f"*{trivia_dict['question']}*\nAn example answer might be '*{trivia_dict['incorrect_answers'][0]}*'."
        await self.send(question_text)
        responses:dict[userid,str] = await self.secret_text_response(
            message = f"{question_text}\nWhat is a possible answer to this qustion that might fool your competitors?")
        options = [trivia_dict['correct_answer']]+list(responses[player] for player in responses)
        options = list(set(options))#remove duplicates
        random.shuffle(options)
        choices:dict[userid,int] = await self.multiple_choice(question_text,options,self.players)
        for option in (option for option in options if not option is trivia_dict['correct_answer']):
            players_who_gave = list(player for player in self.players if responses[player] == option)
            players_who_chose = list(player for player in self.players if options[choices[player]] == option and not player in players_who_gave)
            if not players_who_chose == []:
                await self.send(f"{self.mention(players_who_gave)} provided the answer:\n'{option}'\n and fooled {self.mention(players_who_chose)}.")
                await self.score(players_who_gave,len(players_who_chose)*POINTS_FOOL)
        bonus:dict[userid,int] = {}
        for player_who_gave in (player for player in self.players if responses[player] == trivia_dict['correct_answer']):
            bonus[player_who_gave] = sum(1 for player in self.players if options[choices[player]] == trivia_dict['correct_answer'] and not player == player_who_gave)
        bonus_text = ""
        if bonus:
            bonus_text = (
                f"\n{self.mention(list(bonus))} got {game.wordify_iterable(bonus[player] for player in bonus)}" + 
                " bonus points respectively for providing the correct answer earlier.")
        correct_answer_text = f"The correct answer was:\n'{trivia_dict['correct_answer']}'"
        correct_choice_index = options.index(trivia_dict['correct_answer'])
        correct_players = list(player for player in self.players if choices[player] == correct_choice_index)
        if correct_players:
            await self.send(f"{correct_answer_text}\n{self.mention(correct_players)} got the answer right!{bonus_text}")
            point_dict = self.make_player_dict(POINTS_GUESS,correct_players)
            for player in bonus:
                point_dict[player] += bonus[player]
            await self.score(correct_players,point_dict)
        else:
            await self.send(f"{correct_answer_text}\nNo one got it right :(.")
        
        

            