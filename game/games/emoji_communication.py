from games_config import games_config

from game.game_interface import Game_Interface
from game import PlayerId, PlayerDict
from game.game_bases import Basic_Secret_Message_Base,Rounds_With_Points_Base
import wonderwords
import emoji
import random

CONFIG = games_config['emoji_communications']

NUM_ROUNDS = CONFIG['num_rounds']
NUM_OPTIONS = CONFIG['num_options']

POINTS_FOR_GUESS = CONFIG['points_for_guess']
POINTS_PER_GUESSER = CONFIG['points_per_guesser']
POINTS_FOR_ALL_GUESS = CONFIG['points_for_all_guess']

BONUS_NUM = CONFIG['bonus_num']
BONUS_POINTS_PER_GUESSER = CONFIG['bonus_points_per_guesser']

MAX_EMOJI = CONFIG['max_emoji']

def only_emoji(text:str) -> str:
    emj:list[str] = list(
        token.chars 
        for token in emoji.analyze(text,True,True) 
        if isinstance(token.value,emoji.EmojiMatch)
        )
    emj = emj[0:MAX_EMOJI]
    return "".join(emj)
def num_emoji(text:str) -> int:
    return len(list(
        isinstance(token.value,emoji.EmojiMatch) 
        for token in 
        emoji.analyze("".join(text.split()),True,True)
        ))
def is_only_emoji(text:str) -> bool:
    return not any(
        isinstance(token.value,str) 
        for token in emoji.analyze("".join(text.split()),True,True)
        )

def emoji_response_validator(player:PlayerId,value:str|None) -> tuple[bool,str|None]:
    if value is None:
        return (False,None)
    if not is_only_emoji(value):
        return (False,f"response '{value}' contains non-emoji characters")
    if num_emoji(value) > MAX_EMOJI:
        return (False,f"response '{value}' with {num_emoji(value)} emoji exceeds the maximum number of emoji allowed of {MAX_EMOJI}")
    if num_emoji(value) > BONUS_NUM:
        return (True,f"response '{value}' contains {num_emoji(value)} emoji, if it contained {BONUS_NUM} or fewer, it could be eligible for bonus points")
    return (True,None)


class Emoji_Communication(Basic_Secret_Message_Base,Rounds_With_Points_Base):
    def __init__(self,gh:Game_Interface):
        Basic_Secret_Message_Base.__init__(self,gh)
        Rounds_With_Points_Base.__init__(self,gh)
        self.num_rounds = NUM_ROUNDS
        self.ww_sentence = wonderwords.RandomSentence()
    async def game_intro(self):
        await self.basic_send(
            "# Welcome to a game of emoji communication!\n" +
            f"In this game I will give each of you a sentence in secret and you will do your best to translate it into emojis.\n" +
            f"Please note you can only use at max {MAX_EMOJI}, and all non-emoji characters in your responses will be ignored.\n" +
            f"Then we will go through each players emoji message, and you will attempt to distiguish its orginating sentence from several false ones.\n" +
            f"It is {POINTS_FOR_GUESS} for guessing it correct with {POINTS_PER_GUESSER} for the writer per person who guessed it, but" +
            f"beware! If all players guess it successfully they each get {POINTS_FOR_ALL_GUESS} while the person who wrote it gets none.\n" +
            f"In addition, if the writer used {BONUS_NUM} or less emojis, they earn {BONUS_POINTS_PER_GUESSER} points per person to guess it, if not all do.\n" +
            "That's about it. Lets get started!"
        )
    async def core_game(self):
        player_prompts:PlayerDict[str] = {}
        for current_player in self.unkicked_players:
            player_prompts[current_player] = self.ww_sentence.sentence()
        player_questions = {}
        for current_player in self.unkicked_players:
            player_questions[current_player] = f"Please do your best to convey this sentence through emoji.\n'{player_prompts[current_player]}'"

        emoji_responses = await self.basic_secret_text_response(self.unkicked_players,player_questions,response_validator=emoji_response_validator)

        emoji_prompts = {}
        for current_player in self.unkicked_players:
            emoji_prompts[current_player] = only_emoji(emoji_responses[current_player])
        for current_player in self.unkicked_players:
            players_to_ask = list(player for player in self.unkicked_players if player != current_player)
            options = []
            for i in range(NUM_OPTIONS-1):
                options.append(self.ww_sentence.sentence())
            options.append(player_prompts[current_player])
            random.shuffle(options)

            responses = await self.basic_multiple_choice(
                f"{self.format_players_md([current_player])} emoted '{emoji_prompts[current_player]}' to convey their sentence.\n" +

                "Which sentence was it?",
                options,
                players_to_ask
            )
            correct_players = list(player for player in players_to_ask if options[responses[player]] == player_prompts[current_player])
            correct_text = f"The actual scentence was:\n{player_prompts[current_player]}\n"
            if len(correct_players) == 0:#no one was correct
                await self.basic_send(f"{correct_text}No one got it right. No points.")
            elif len(correct_players) == len(players_to_ask):#all right
                await self.basic_send(
                    f"{correct_text}Since everyone got it right, each player only gets " +
                    f"{POINTS_FOR_ALL_GUESS}, except {self.format_players_md([current_player])} who gets none.")
                await self.score(correct_players,POINTS_FOR_ALL_GUESS,mute = True)
            else:
                points = POINTS_PER_GUESSER*len(correct_players)
                bonus_text = ""
                if num_emoji(emoji_prompts[current_player]) <= BONUS_NUM:
                    points = BONUS_POINTS_PER_GUESSER*len(correct_players)
                    bonus_text = f", and achieving the bonus for using less than {BONUS_NUM} emojis,"

                await self.basic_send(
                    f"{correct_text}{self.format_players_md(correct_players)} got it right each earning {POINTS_FOR_GUESS} point(s).\n" +
                    f"For guiding them so well{bonus_text} {self.format_players_md([current_player])} earned {points} point(s)."

                )
                await self.score(correct_players,POINTS_FOR_GUESS,mute = True)
                await self.score(current_player,points,mute = True)
                



            