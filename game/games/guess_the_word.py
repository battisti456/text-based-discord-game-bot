import random
from typing import Annotated, override

from config_system_battisti456.config_item import Bool, Integer

from config import Config
from game.components.game_interface import Game_Interface
from game.components.participant import Player, PlayerDict, mention_participants
from game.components.send import Address, sendables
from game.game_bases import (
    Game_Word_Base,
    Rounds_With_Points_Base,
)
from utils.grammar import wordify_iterable
from utils.word_tools import (
    DefinitionList,
    SimplePartOfSpeech,
    definition_dict_to_list,
)


class config(Config):
    num_rounds:Annotated[int,Integer(level=1,min_value=1)] = 5
    min_word_len:Annotated[int,Integer(level=1,min_value=1,max_value=12)] = 5
    max_word_len:Annotated[int,Integer(level=1,min_value=1)] = 12
    num_definitions:Annotated[int,Integer(level=1,min_value=1)] = 3
    guess_feedback:Annotated[bool,Bool(level=1)] = True
    length_hint:Annotated[bool,Bool(level=1)] = True

class Guess_The_Word(Game_Word_Base, Rounds_With_Points_Base):
    def __init__(self,gi:Game_Interface):
        Game_Word_Base.__init__(self,gi)
        Rounds_With_Points_Base.__init__(self,gi)
        self.num_rounds = config.num_rounds
    @override
    async def game_intro(self):
        await self.say(
            "# This is a game of guessing the word!\n" +
            f"I will generate a random secret word of a length from {config.min_word_len}-{config.max_word_len}.\n" +
            f"Then I will give you {config.num_definitions} different definitions for it.\n" +
            "After each definition, you will be given a chance to guess the word being defined.\n" +
            "The fewer definitions you need, the more points you will get for a success.\n" +
            f"This will continue across {config.num_rounds} different word(s).\n" + 
            "The highest points at the end is the winner!\n" +
            "CAUTION: Sometimes words can be spelled other ways....")
    @override
    async def core_round(self):
        definition_list:DefinitionList = []
        type_set:set[SimplePartOfSpeech] = set()
        secret_word:str= ""
        while len(definition_list) < config.num_definitions:
            secret_word = self.random_valid_word(random.randint(config.min_word_len,config.max_word_len))
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
        if config.length_hint:
            len_text = f" of length {len(secret_word)} and type(s) {wordify_iterable(type_set)}"
        random.shuffle(definition_list)
        players_not_guessed:list[Player] = list(self.unkicked_players)
        await self.say(f"The secret word{len_text} has been chosen!")
        for sub_round in range(config.num_definitions):
            def_str = self.definition_string([definition_list[sub_round]])
            await self.say(f"### Here is definition #{sub_round + 1} of the word{len_text}:\n{def_str}")
            if config.guess_feedback:
                for player in self.unkicked_players:
                    if player in players_not_guessed and (any(player_hint_letter[player]) or any(global_hint_letter)):
                        feedback = ""
                        for j in range(len(secret_word)):
                            if player_hint_letter[player][j] or global_hint_letter[j]:
                                feedback += secret_word[j]
                            else:
                                feedback += "\\_"
                        address:Address = await self.sender.generate_address(frozenset([player]))
                        await self.sender(sendables.Text_Only(text=f"Your current feedback is '{feedback}'."),address)
            responses:PlayerDict[str] = await self.basic_text_response(
                who_chooses=players_not_guessed,
                content=f"**What word{len_text} is this definition for?**\n{def_str}")
            if len(responses.keys()) == 0:#no responses, everyone has been kicked
                await self.say(f"Since no one submitted a response, I will reveal the correct answer was '{secret_word}'.")
                return
            correct_players:list[Player] = list(player for player,response in responses.items() if response.lower() == secret_word)
            if config.guess_feedback:
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
                    await self.say("Not a single person got new feedback this round, so I will be providing everyone some.\n" + 
                                    f"Our current public feedback is '{slot_text}'.")
            if any(correct_players):
                await self.say(f"{mention_participants(correct_players)} got it correct!")
                players_not_guessed = list(set(responses.keys()) - set(correct_players))
                await self.announce_and_receive_score(correct_players,config.num_definitions-sub_round)
            else:
                await self.say("No one got it correct.")
            if len(players_not_guessed) == 0:
                await self.say("Everyone has guessed the word!")
                break
        await self.say(f"The word was '{secret_word}'.")
        if(len(definition_list) > config.num_definitions):
            await self.say("Some unused definitions included:\n" +
                            self.definition_string(definition_list[config.num_definitions:]))
                
        
            

            
            