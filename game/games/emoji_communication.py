import game
from game import userid
from game.game_bases import Secret_Message_Base,Rounds_With_Points_Base
import wonderwords
import emoji
import random

NUM_ROUNDS = 1
NUM_OPTIONS = 5

POINTS_FOR_GUESS = 2
POINTS_PER_GUESSER = 1
POINTS_FOR_ALL_GUESS = 1

MAX_EMOJI = 10

def only_emoji(text:str) -> str:
    emj:list[str] = list(token.chars for token in emoji.analyze(text))
    emj = emj[0:MAX_EMOJI]
    return "".join(emj)

class Emoji_Communication(Secret_Message_Base,Rounds_With_Points_Base):
    def __init__(self,gh:game.GH):
        Secret_Message_Base.__init__(self,gh)
        Rounds_With_Points_Base.__init__(self,gh)
        self.num_rounds = NUM_ROUNDS
        self.ww_sentence = wonderwords.RandomSentence()
    async def game_intro(self):
        await self.send(
            "# Welcome to a game of emoji communication!\n" +
            f"In this game I will give each of you a sentence in secret and you will do your best to translate it into emojis.\n" +
            f"Please note you can only use at max {MAX_EMOJI}, and all non-emoji characters in your responses will be ignored.\n" +
            f"Then we will go through each players emoji message, and you will attempt to distiguish its orginating sentence from several false ones.\n" +
            f"It is {POINTS_FOR_GUESS} for guessing it correct with {POINTS_PER_GUESSER} for the writer per person who guessed it, but" +
            f"beware! If all players guess it successfully they each get {POINTS_FOR_ALL_GUESS} while the person who wrote it gets none.\n" +
            "That's about it. Lets get started!"
        )
    async def core_game(self):
        player_prompts:dict[userid,str] = {}
        for current_player in self.players:
            player_prompts[current_player] = self.ww_sentence.sentence()
        player_questions = {}
        for current_player in self.players:
            player_questions[current_player] = f"Please do your best to convey this sentence through emoji.\n'{player_prompts[current_player]}'"
        emoji_responses = await self.secret_text_response(self.players,player_questions)
        emoji_prompts = {}
        for current_player in self.players:
            emoji_prompts[current_player] = only_emoji(emoji_responses[current_player])
        for current_player in self.players:
            players_to_ask = list(player for player in self.players if player != current_player)
            options = []
            for i in range(NUM_OPTIONS-1):
                options.append(self.ww_sentence.sentence())
            options.append(player_prompts[current_player])
            random.shuffle(options)
            responses = await self.multiple_choice(
                f"{self.mention(current_player)} emoted '{emoji_prompts[current_player]}' to convey their sentence.\n" +
                "Which sentence was it?",
                options,
                players_to_ask
            )
            correct_players = list(player for player in players_to_ask if options[responses[player]] == player_prompts[current_player])
            correct_text = f"The actual scentence was:\n{player_prompts[current_player]}\n"
            if len(correct_players) == 0:#no one was correct
                await self.send(f"{correct_text}No one got it right. No points.")
            elif len(correct_players) == len(players_to_ask):#all right
                await self.send(
                    f"{correct_text}Since everyone got it right, each player only gets " +
                    f"{POINTS_FOR_ALL_GUESS}, except {self.mention(current_player)} who gets none.")
                await self.score(correct_players,POINTS_FOR_ALL_GUESS,mute = True)
            else:
                await self.send(
                    f"{correct_text}{self.mention(correct_players)} got it right each earning {POINTS_FOR_GUESS} point(s).\n" +
                    f"For guiding them so well {self.mention(current_player)} earned {POINTS_PER_GUESSER*len(correct_players)} point(s)."
                )
                await self.score(correct_players,POINTS_FOR_GUESS,mute = True)
                await self.score(current_player,POINTS_PER_GUESSER*len(correct_players),mute = True)
                



            
