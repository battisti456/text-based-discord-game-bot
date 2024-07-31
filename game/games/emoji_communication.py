import random
from typing import override, Annotated

import emoji
from config_system_battisti456.config_item import Integer, IntegerRange, Bool
from config import Config
from game.components.game_interface import Game_Interface
from game.components.participant import Player, PlayerDict, mention_participants
from game.components.send import sendables
from game.components.send.interaction import Send_Text
from game.game_bases import (
    Game_Word_Base,
    Rounds_With_Points_Base,
)
from utils.grammar import nice_sentence
from utils.word_tools import find_random_related_sentences

class config(Config):
    num_options:Annotated[int,Integer(level=1,min_value=1)] = 5
    num_rounds:Annotated[int,Integer(level=1,min_value=2)] = 1
    points_per_guess:Annotated[int,Integer(level=1)] = 2
    points_per_guesser:Annotated[int,Integer(level=1)] = 1
    points_for_all_guess:Annotated[int,Integer(level=1)] = 1
    bonus_num:Annotated[int,Integer(level=1)] = 3
    bonus_points_per_guesser:Annotated[int,Integer(level=1)] = 2
    max_emoji:Annotated[int,Integer(level=1,min_value=1)] = 10
    swap_range:Annotated[tuple[int,int],IntegerRange(level=1,min_value=1)] = (2,3)
    give_avoid_options:Annotated[bool,Bool(level=1)] = True

#region emoji funcs
def only_emoji(text:str) -> str:
    emj:list[str] = list(
        token.chars 
        for token in emoji.analyze(text,True,True) 
        if isinstance(token.value,emoji.EmojiMatch)
        )
    emj = emj[0:config.max_emoji]
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

def emoji_response_validator(player:Player,raw_value:Send_Text|None) -> tuple[bool,str|None]:
    if raw_value is None:
        return (False,None)
    value = raw_value.text
    if not is_only_emoji(value):
        return (False,f"response '{value}' contains non-emoji characters")
    if num_emoji(value) > config.max_emoji:
        return (False,f"response '{value}' with {num_emoji(value)} emoji exceeds the maximum number of emoji allowed of {config.max_emoji}")
    if num_emoji(value) > config.bonus_num:
        return (True,f"response '{value}' contains {num_emoji(value)} emoji, if it contained {config.bonus_num} or fewer, it could be eligible for bonus points")
    return (True,None)
#endregion

class Emoji_Communication(Rounds_With_Points_Base,Game_Word_Base):
    def __init__(self,gh:Game_Interface):
        Rounds_With_Points_Base.__init__(self,gh)
        Game_Word_Base.__init__(self,gh)
        self.num_rounds = config.num_rounds
    @override
    async def game_intro(self):
        await self.say(
            "# Welcome to a game of emoji communication!\n" +
            "In this game I will give each of you a sentence in secret and you will do your best to translate it into emojis.\n" +
            f"Please note you can only use at max {config.max_emoji}, and all non-emoji characters in your responses will be ignored.\n" +
            "Then we will go through each players emoji message, and you will attempt to distinguish its originating sentence from several false ones.\n" +
            f"It is {config.points_per_guess} for guessing it correct with {config.points_per_guesser} for the writer per person who guessed it, but" +
            f"beware! If all players guess it successfully they each get {config.points_for_all_guess} while the person who wrote it gets none.\n" +
            f"In addition, if the writer used {config.bonus_num} or less emojis, they earn {config.bonus_points_per_guesser} points per person to guess it, if not all do.\n" +
            "That's about it. Lets get started!"
        )
    @override
    async def core_round(self):
        base_str:PlayerDict[str] = {}
        opt_str:PlayerDict[list[str]] = {}
        for player in self.unkicked_players:
            while player not in base_str:
                raw = self.ww_sentence.sentence()
                sentence = list(word for word in raw.lower()[:-1].split())
                related = find_random_related_sentences(
                    sentence,
                    list(range(config.swap_range[0],config.swap_range[1]+1)),
                    num_sentences=config.num_options
                    )
                if len(related) < config.num_options:
                    continue
                base_str[player] = nice_sentence(sentence)
                opt_str[player] = list(nice_sentence(rel) for rel in related[:config.num_options])

        player_questions:PlayerDict[str] = {}
        for current_player in self.unkicked_players:
            avoid_text:str = ""
            if config.give_avoid_options:
                avoid_text = "\nHere are other sentences the other players will see for your question:\n"
                for sentence in opt_str[current_player][1:]:
                    avoid_text += sentence + '\n'
            player_questions[current_player] = f"Please do your best to convey this sentence through emoji.\n'{opt_str[current_player][0]}'{avoid_text}"
            address = await self.sender.generate_address(frozenset([current_player]))
            await self.sender(sendables.Text_Only(text=player_questions[current_player]),address)

        emoji_responses = await self.basic_text_response(
            content="Input your emojis here!",
            who_chooses = self.unkicked_players,
            response_validator=emoji_response_validator)

        emoji_prompts:PlayerDict[str] = {}
        for current_player in self.unkicked_players:
            emoji_prompts[current_player] = only_emoji(emoji_responses[current_player])
        for current_player in self.unkicked_players:
            players_to_ask = list(player for player in self.unkicked_players if player != current_player)
            options:list[str] = list(opt_str[current_player])
            random.shuffle(options)

            responses = await self.basic_multiple_choice(
                f"{mention_participants([current_player])} emoted '{emoji_prompts[current_player]}' to convey their sentence.\n" +

                "Which sentence was it?",
                options,
                players_to_ask
            )
            correct_players = list(player for player in players_to_ask if options[responses[player]] == opt_str[current_player][0])
            correct_text = f"The actual sentence was:\n{opt_str[current_player][0]}\n"
            if len(correct_players) == 0:#no one was correct
                await self.say(f"{correct_text}No one got it right. No points.")
            elif len(correct_players) == len(players_to_ask):#all right
                await self.say(
                    f"{correct_text}Since everyone got it right, each player only gets " +
                    f"{config.points_for_all_guess}, except {mention_participants([current_player])} who gets none.")
                await self.score(correct_players,config.points_for_all_guess,mute = True)
            else:
                points = config.points_per_guesser*len(correct_players)
                bonus_text = ""
                if num_emoji(emoji_prompts[current_player]) <= config.bonus_num:
                    points = config.bonus_points_per_guesser*len(correct_players)
                    bonus_text = f", and achieving the bonus for using less than {config.bonus_num} emojis,"

                await self.say(
                    f"{correct_text}{mention_participants(correct_players)} got it right each earning {config.points_per_guess} point(s).\n" +
                    f"For guiding them so well{bonus_text} {mention_participants([current_player])} earned {points} point(s)."

                )
                await self.score(correct_players,config.points_per_guess,mute = True)
                await self.score(current_player,points,mute = True)
                



            