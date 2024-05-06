from game.utils.common import L

from nltk.corpus import wordnet
from nltk.tag.perceptron import PerceptronTagger
from nltk.corpus.reader.wordnet import Synset, Lemma
from word_forms.word_forms import get_word_forms #type: ignore
from dataclasses import dataclass
import random

from typing import Literal, overload, get_args

type SimplePartOfSpeach = Literal['Noun','Verb','Adjective','Adverb']

type DefinitionDict = dict[SimplePartOfSpeach,list[str]]
type DefinitionList = list[tuple[SimplePartOfSpeach,str]]

type Word = str
type Sentence = list[Word]

UNDEFINED_TEXT = "UNDEFINED"
WORDNET_POS_MAP:dict[str,SimplePartOfSpeach]  = {
    'n' : 'Noun',
    's' : 'Adjective',#difference between s and a has someting to do synset clusters, probably not important
    'a' : 'Adjective',
    'r' : 'Adverb',
    'v' : 'Verb'
}
MAX_RANDOM_SCENTENCE_LOOPS = 1000

@dataclass(frozen=True)
class Definition():
    synset:Synset
    @property
    def definition(self) -> str:
        definition:str|None= self.synset.definition()
        return definition if isinstance(definition,str) else UNDEFINED_TEXT
    @property
    def examples(self) -> list[str]:
        examples:list[str]|None = self.synset.examples() 
        return examples if isinstance(examples,list) else []
    @property
    def pos(self) -> SimplePartOfSpeach:
        return WORDNET_POS_MAP[self.synset.pos()]#type:ignore
    def is_definition(self,word:str) -> bool:
        return word in self.synset.lemma_names()
@dataclass(frozen=True)
class Word_Definition():
    word:str
    definitions:frozenset[Definition]
    def to_dict(self) -> DefinitionDict:
        to_return:DefinitionDict = {}
        for definition in self.definitions:
            if not definition.pos in to_return:
                to_return[definition.pos] = []
            to_return[definition.pos].append(definition.definition)
        return to_return
    def to_list(self) -> DefinitionList:
        return list(
            (definition.pos,definition.definition) 
            for definition in self.definitions
        )

tagger = PerceptronTagger()
#region WordRelationships
WordRelationship = Literal[
    'hyponym',#a word with a more specific meaning than ____
    'hypernym',#a word with a more broad meaning than ____
    'part_meronym',#a word associated with a part of ____
    'member_meronym',#a word associated with the whole of ____
    'part_holonym',#a word that represents the whole of a part of ____
    'member_holonym',#a word that represents the whole of ____
    'substance_holonym',#a word that reperesents the composing whole of a substance of ____
    'synonym',# word with the same or similar meaning
    'antonym',#a word with the opposite meaning
]
#endregion
ALL_RELATIONSHIPS:tuple[WordRelationship,...] = get_args(WordRelationship)
#region find_related
@overload
def find_related_words(word:str,*properties:WordRelationship) -> frozenset[str]:
    ...
@overload
def find_related_words(word:Lemma|Synset,*properties:WordRelationship) -> frozenset[Lemma]:
    ...
def find_related_words(word:Word|Lemma|Synset,*properties:WordRelationship) -> frozenset[Word]|frozenset[Lemma]:
    if len(properties) == 0:
        properties = ALL_RELATIONSHIPS
    synsets:list[Synset]
    if isinstance(word,Synset):
        synsets = [word]
    else:
        synsets = wordnet.synsets(word) #type: ignore
    out_words:list[Lemma|Synset] = []
    for synset in synsets:
        for property in properties:
            match(property):
                case 'hypernym':
                    out_words += synset.hypernyms()
                case 'hyponym':
                    out_words += synset.hyponyms()
                case 'part_meronym':
                    out_words += synset.part_meronyms()
                case 'member_meronym':
                    out_words += synset.member_meronyms()
                case 'part_holonym':
                    out_words += synset.part_holonyms()
                case 'member_holonym':
                    out_words += synset.member_holonyms()
                case 'substance_holonym':
                    out_words += synset.substance_holonyms()
                case 'synonym':
                    out_words += L(synset.lemmas())
                case 'antonym':
                    synonyms:list[Lemma] = L(synset.lemmas())
                    for synonym in synonyms:
                        out_words += synonym.antonyms()
    lemmas:list[Lemma] = []
    for word_out in out_words:
        if isinstance(word_out,Synset):
            lemmas += L(word_out.lemmas())
        else:
            lemmas.append(word_out)
    if isinstance(word,str):
        return frozenset(lemma.name()  for lemma in lemmas)
    else:
        return frozenset(lemmas)
#endregion

def find_related_words_in_context(
        word_index:int,
        context:list[str],
        relationships:list[WordRelationship] = [],
        confidence_threshold:float = 0.95
        ) -> frozenset[Word]:
    """
    find words related through the given relationships to context[word_index]

    word_index: the intex in context of the word to find related terms to

    context: the words of the sentence for the context of the relevant word

    relationships: the relationships to include, by default includes ALL_RELATIONSHIPS

    confidence_threshold: a value between 0 and 1 representing the level of confidence the program has that the returned words make sense in context
    """
    tags = tagger.tag(context,return_conf=True)

    default_cft = list(min(tag[2],confidence_threshold) for tag in tags)
    word_form_type:str = tags[word_index][1][0].lower()

    considered:set[str] = set()
    success:set[str] = set()

    related:frozenset[str] = find_related_words(context[word_index],*relationships)
    for word in related:
        form_dict = get_word_forms(word)
        forms:set[str] = set()
        if word_form_type in form_dict:
            forms = form_dict[word_form_type]
        forms.add(word)
        for var in forms:
            if var in considered:
                continue
            considered.add(var)
            cft = list(default_cft)
            words = list(context)
            if '_' in var:
                names = var.split('_')
                words = words[:word_index] + names + words[word_index+1:]
                cft = cft[:word_index] + [cft[word_index]]*len(names) + cft[word_index+1:]
            else:
                words[word_index] = var
            form_tags = tagger.tag(words,return_conf=True)
            if any(form_tags[j][2] < cft[j] for j in range(len(words))):
                continue
            if not '_' in var and not all(tags[j][1] == form_tags[j][1] for j in range(len(words))):
                continue
            success.add(var)
    if context[word_index] in success:
        success.remove(context[word_index])
    return frozenset(success)
def validate_scentence(scentence:Sentence,min_conf = 0.95) -> bool:
    return not any(
        conf < min_conf for _,_,conf in tagger.tag(scentence,return_conf=True)
    )

def find_random_related_scentences(
            sentence:Sentence,
            num_to_change:list[int],
            num_scentences:int,
            relationships:list[WordRelationship] = []
            ) -> list[list[str]]:
        option_groups:list[list[str]] = []
        for i in range(len(sentence)):
            option_groups.append(
                [sentence[i]] + list(find_related_words_in_context(
                    i,sentence,relationships
                ))
            )
        if len(option_groups) == 0:
            return []
        combos:set[tuple[int,...]] = set()
        num_loops:int = 0
        _valid_options = tuple(
            i for i in range(1,len(option_groups)) if len(option_groups) > 1
        )
        _valid_num_to_change = tuple(
            n for n in num_to_change if n <= len(_valid_options)
        )
        if len(_valid_num_to_change) == 0:
            return []
        while len(combos) < num_scentences and num_loops < MAX_RANDOM_SCENTENCE_LOOPS:
            indexes_to_change = random.sample(_valid_options,random.choice(_valid_num_to_change))
            combo:tuple[int,...] = tuple(
                0 if i not in indexes_to_change else random.randint(0,len(option_groups[i])-1) for i in range(len(option_groups))
            )
            scen = list(option_groups[i][combo[i]] for i in range(len(option_groups)))
            if not validate_scentence(scen):
                continue
            combos.add(combo)
        return list(list(option_groups[i][combo[i]] for i in range(len(combo))) for combo in combos)

def get_word_definition(word:Word) -> Word_Definition:
    synsets:list[Synset] = L(wordnet.synsets(word))
    return Word_Definition(
        word,
        frozenset(
            Definition(synset) for synset in synsets
        )
    )
def definition_dict_to_list(value:DefinitionDict) -> DefinitionList:
    to_return:DefinitionList = []
    for pos in value:
        for _def in value[pos]:
            to_return.append((pos,_def))
    return to_return