import random
from typing import override

from config.games_config import games_config
from game.components.game_interface import Game_Interface
from game.game_bases import (
    Basic_Secret_Message_Base,
    Game_Word_Base,
    Rounds_With_Points_Base,
)
from utils.grammar import wordify_iterable
from utils.types import PlayerDict, PlayerId
from utils.word_tools import (
    DefinitionList,
    SimplePartOfSpeech,
    definition_dict_to_list,
)

CONFIG = games_config['guess_the_word']

NUM_ROUNDS = CONFIG['num_rounds']
MIN_WORD_LEN = CONFIG['min_word_len']
MAX_WORD_LEN = CONFIG['max_word_len']
NUM_DEFINITIONS = CONFIG['num_definitions']

GUESS_FEEDBACK = CONFIG['guess_feedback']
LENGTH_HINT = CONFIG['length_hint']

class Guess_The_Word(Game_Word_Base, Basic_Secret_Message_Base, Rounds_With_Points_Base):
    def __init__(self,gi:Game_Interface):
        Game_Word_Base.__init__(self,gi)
        Basic_Secret_Message_Base.__init__(self,gi)
        Rounds_With_Points_Base.__init__(self,gi)
        self.num_rounds = NUM_ROUNDS
    @override
    async def game_intro(self):
        await self.basic_send(
            "# This is a game of guessing the word!\n" +
            f"I will generate a random secret word of a length from {MIN_WORD_LEN}-{MAX_WORD_LEN}.\n" +
            f"Then I will give you {NUM_DEFINITIONS} different definitions for it.\n" +
            "After each definition, you will be given a chance to guess the word being defined.\n" +
            "The fewer definitions you need, the more points you will get for a success.\n" +
            f"This will continue across {NUM_ROUNDS} different word(s).\n" + 
            "The highest points at the end is the winner!\n" +
            "CAUTION: Sometimes words can be spelled other ways....")
    @override
    async def core_game(self):
        definition_list:DefinitionList = []
        type_set:set[SimplePartOfSpeech] = set()
        secret_word:str= ""
        while len(definition_list) < NUM_DEFINITIONS:
            secret_word = self.random_valid_word(random.randint(MIN_WORD_LEN,MAX_WORD_LEN))
            definition_dict = self.define(secret_word)
            if definition_dict is None:
                continue
            definition_list = definition_dict_to_list(definition_dict)
            type_set = set(definition_dict)
        len_text = ""
        global_hint_letter = [False]*len(secret_word)
        player_hint_letter:PlayerDict[list[bool]] = {}
        for player in self.unkicked_players:
            player_hint_letter[player] = [False]*len(secret_word)
        if LENGTH_HINT:
            len_text = f" of length {len(secret_word)} and type(s) {wordify_iterable(type_set)}"
        random.shuffle(definition_list)
        players_not_guessed:list[PlayerId] = list(self.unkicked_players)
        await self.basic_send(f"The secret word{len_text} has been chosen!")
        for sub_round in range(NUM_DEFINITIONS):
            def_str = self.definition_string([definition_list[sub_round]])
            await self.basic_send(f"### Here is definition #{sub_round + 1} of the word{len_text}:\n{def_str}")
            if GUESS_FEEDBACK:
                for player in self.unkicked_players:
                    if player in players_not_guessed and (any(player_hint_letter[player]) or any(global_hint_letter)):
                        feedback = ""
                        for j in range(len(secret_word)):
                            if player_hint_letter[player][j] or global_hint_letter[j]:
                                feedback += secret_word[j]
                            else:
                                feedback += "\\_"
                        await self.basic_secret_send(player,f"Your current feedback is '{feedback}'.")
            responses:PlayerDict[str] = await self.basic_secret_text_response(players_not_guessed,f"**What word{len_text} is this definition for?**\n{def_str}")
            if len(responses.keys()) == 0:#no responses, everyone has been kicked
                await self.basic_send(f"Since no one submitted a response, I will reveal the correct answer was '{secret_word}'.")
                return
            correct_players:list[PlayerId] = list(player for player,response in responses.items() if response.lower() == secret_word)
            if GUESS_FEEDBACK:
                no_success = (len(correct_players) == 0)
                for player in responses.keys():
                    if player not in correct_players:
                        response = responses[player]
                        for j in range(min(len(response),len(secret_word))):
                            if response[j] == secret_word[j] and not (player_hint_letter[player][j] or global_hint_letter[j]):#doesn't seem to work right
                                player_hint_letter[player][j] = True
                                no_success = False
                if no_success and not all(global_hint_letter):
                    j = random.randint(0,len(global_hint_letter)-1)
                    while global_hint_letter[j]:
                        j = (j+1)%len(global_hint_letter)
                    global_hint_letter[j] = True
                    slot_text = ""
                    for j in range(len(secret_word)):
                        if global_hint_letter[j]:
                            slot_text += secret_word[j]
                        else:
                            slot_text += "\\_"
                    await self.basic_send("Not a single person got new feedback this round, so I will be providing everyone some.\n" + 
                                    f"Our current public feedback is '{slot_text}'.")
            if any(correct_players):
                await self.basic_send(f"{self.format_players_md(correct_players)} got it correct!")
                players_not_guessed = list(set(responses.keys()) - set(correct_players))
                await self.announce_and_receive_score(correct_players,NUM_DEFINITIONS-sub_round)
            else:
                await self.basic_send("No one got it correct.")
            if len(players_not_guessed) == 0:
                await self.basic_send("Everyone has guessed the word!")
                break
        await self.basic_send(f"The word was '{secret_word}'.")
        if(len(definition_list) > NUM_DEFINITIONS):
            await self.basic_send("Some unused definitions included:\n" +
                            self.definition_string(definition_list[NUM_DEFINITIONS:]))
                
        
            

            
            