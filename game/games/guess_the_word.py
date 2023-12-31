import game
from game import PlayerId

from game.game_bases import Dictionary_Base, Secret_Message_Base, Rounds_With_Points_Base

import random

NUM_ROUNDS = 1
MIN_WORD_LEN = 6
MAX_WORD_LEN = 12
NUM_DEFINITIONS = 6

GUESS_FEEDBACK = True
LENGTH_HINT = True

class Guess_The_Word(Dictionary_Base,Secret_Message_Base, Rounds_With_Points_Base):
    def __init__(self,gh:game.GH):
        Dictionary_Base.__init__(self,gh)
        Secret_Message_Base.__init__(self,gh)
        Rounds_With_Points_Base.__init__(self,gh)
        self.num_rounds = NUM_ROUNDS
    async def game_intro(self):
        await self.basic_send("# This is a game of guessing the word!\n" +
                        f"I will generate a random secret word of a length from {MIN_WORD_LEN}-{MAX_WORD_LEN}.\n" +
                        f"Then I will give you {NUM_DEFINITIONS} different definitions for it.\n" +
                        "After each definintion, you will be given a chance to guess the word being defined.\n" +
                        "The fewer definitions you need, the more points you will get for a success.\n" +
                        f"This will continue across {NUM_ROUNDS} different word(s).\n" + 
                        "The highest points at the end is the winner!\n" +
                        "CAUTION: Sometimes words can be spelled other ways....")
    async def core_game(self):
        definition_list = []
        while len(definition_list) < NUM_DEFINITIONS:
            secret_word:str = self.random_word(random.randint(MIN_WORD_LEN,MAX_WORD_LEN))
            definition_dict = self.define(secret_word)
            type_set = set()
            if definition_dict is None:
                continue
            definition_list:list[tuple[str,str]] = []
            for word_type in definition_dict:
                for definition in definition_dict[word_type]:
                    definition_list.append((word_type.lower(),definition))
                    type_set.add(word_type.lower())
        len_text = ""
        global_hint_letter = [False]*len(secret_word)
        player_hint_letter:dict[int,list[bool]] = {}
        for player in self.players:
            player_hint_letter[player] = [False]*len(secret_word)
        if LENGTH_HINT:
            len_text = f" of length {len(secret_word)} and type(s) {game.wordify_iterable(type_set)}"
        random.shuffle(definition_list)
        players_not_guessed:list[int] = list(self.players)
        await self.basic_send(f"The secret word{len_text} has been chosen!")
        for sub_round in range(NUM_DEFINITIONS):
            def_str = self.definition_string(definition_list[sub_round])
            await self.basic_send(f"Here is definition #{sub_round + 1} of the word{len_text}:\n{def_str}")
            if GUESS_FEEDBACK:
                for player in self.players:
                    if player in players_not_guessed and (any(player_hint_letter[player]) or any(global_hint_letter)):
                        feedback = ""
                        for j in range(len(secret_word)):
                            if player_hint_letter[player][j] or global_hint_letter[j]:
                                feedback += secret_word[j]
                            else:
                                feedback += "\_"
                        await self.secret_send(player,f"Your current feedback is '{feedback}'.")
            responses:dict[PlayerId,str] = await self.secret_text_response(players_not_guessed,f"What word{len_text} is this definition for?\n{def_str}")
            correct_players:list[int] = list(player for player in players_not_guessed if responses[player].lower() == secret_word)
            if GUESS_FEEDBACK:
                no_success = (len(correct_players) == 0)
                for player in players_not_guessed:
                    if not player in correct_players:
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
                            slot_text += "\_"
                    await self.basic_send(f"Not a single person got new feedback this round, so I will be providing everyone some.\n" + 
                                    f"Our current public feedback is '{slot_text}'.")
            if any(correct_players):
                await self.basic_send(f"{self.format_players_md(correct_players)} got it correct!")
                for player in correct_players:
                    players_not_guessed.remove(player)
                await self.score(correct_players,NUM_DEFINITIONS-sub_round)
            else:
                await self.basic_send("No one got it correct.")
            if len(players_not_guessed) == 0:
                await self.basic_send("Everyone has guessed the word!")
                break
        await self.basic_send(f"The word was '{secret_word}'.")
        if(len(definition_list) > NUM_DEFINITIONS):
            await self.basic_send(f"Some unused definitions included:\n" +
                            self.definition_string(definition_list[NUM_DEFINITIONS:]))
                
        
            

            
            