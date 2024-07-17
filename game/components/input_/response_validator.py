from typing import Any, Generic, Iterable, Mapping, Optional, Protocol, TypeVar

from profanity_check import predict_prob

from config.config import config
from game.components.participant import Participant, ParticipantVar
from game.components.send.interaction import Select_Options, Send_Text

T = TypeVar('T')
type Validation = tuple[bool,str|None]
"""
a tuple with values bool, and str or None

the bool determines whether a given response was valid, true for allowed, false for not allowed

the str|None determines the feedback given; None results in no feedback, otherwise the str is returned as feedback to the player
"""

class ResponseValidator(Generic[T,ParticipantVar],Protocol): # type: ignore
    def __call__(self, participant:ParticipantVar, value:T|None,/) -> Validation:
        ...

def not_none(participant:Participant,data:Any) -> Validation:
    return data is not None , None

def text_validator_maker(
        is_substr_of:Optional[str] = None,
        is_supstr_of:Optional[str] = None,
        max_length:Optional[int] = None,#inclusive
        min_length:Optional[int] = None,#inclusive
        is_alpha:Optional[bool] = None,
        is_alnum:Optional[bool] = None,
        is_decimal:Optional[bool] = None,
        is_digit:Optional[bool] = None,
        is_in:Optional[list[str]] = None,
        not_is_in:Optional[list[str]] = None,
        is_composed_of:Optional[str] = None,
        is_strictly_composed_of:Optional[str] = None,
        check_lower_case:bool = False,
        min_num_words:Optional[int] = None,
        max_num_words:Optional[int] = None
        
) -> ResponseValidator[Send_Text,Any]:
    """creates a response validator for str's matching given validation, and with feedback given on problems with the input"""
    def validator(participant:Any,raw_value:Optional[Send_Text]) -> Validation:
        if raw_value is None:
            return (False,None)
        value = raw_value.text
        if check_lower_case:
            value = value.lower()
        if predict_prob([value])[0] >= config['profanity_threshold']:
            return (False,"given value set off the profanity filter")
        if is_in is not None:
            if value not in is_in:
                return (False,f"given value '{value}' not in acceptable values")
        if not_is_in is not None:
            if value in not_is_in:
                return (False,f"given value '{value}' is a banned value")
        if is_substr_of is not None:
            if value not in is_substr_of:
                return (False,f"given value '{value}' not in '{is_substr_of}'")
        if is_supstr_of is not None:
            if is_supstr_of not in value:
                return (False,f"'{is_supstr_of}' not in given value '{value}'")
        if max_length is not None:
            if len(value) > max_length:
                return (False,f"given value '{value}' of length {len(value)} exceeds the maximum length of {max_length}")
        if min_length is not None:
            if len(value) < min_length:
                return (False,f"given value '{value}' of length {len(value)} is below the minimum length of {min_length}")
        if is_alpha is not None:
            if not value.isalpha():
                return (False,f"given value '{value}' contains non-alphabetical characters")
        if is_alnum is not None:
            if not value.isalnum():
                return (False,f"given value '{value}' contains characters which are neither alphabetic or numeric")
        if is_decimal is not None:
            if not value.isdecimal():
                return (False,f"given value '{value}' contains non-decimal characters")
        if is_digit is not None:
            if not value.isdigit():
                return (False,f"given value '{value}' is not a digit")
        if is_composed_of is not None:
            if not all(letter in is_composed_of for letter in value):
                return (False,f"given value '{value}' contains characters not found in '{is_composed_of}'")
        if is_strictly_composed_of is not None:
            list_letters = list(is_strictly_composed_of)
            for letter in value:
                if letter in list_letters:
                    list_letters.remove(letter)
                else:
                    return (False,f"given value '{value}' contains more characters than are found in '{is_strictly_composed_of}'")
        num_words =  len(value.split())
        if min_num_words is not None:
            if num_words < min_num_words:
                return (False,f"given value '{value}' contains {num_words} word(s) which is less than the minimum of {min_num_words} words")
        if max_num_words is not None:
            if num_words > max_num_words:
                return (False,f"given value '{value}' contains {num_words} word(s) which is more than the maximum of {min_num_words} words")
        return (True,None)
    return validator
def select_validation_maker(
        *,
        can_select:Optional[Mapping[ParticipantVar,Iterable[int]]] = None,
        min_select:Optional[int] = None,
        max_select:Optional[int] = None
) -> ResponseValidator[Select_Options,ParticipantVar]:
    def validator(participant:ParticipantVar,raw_value:Optional[Select_Options]) -> Validation:
        if raw_value is None:
            return (False,None)
        if can_select is not None:
            for index,option in zip(raw_value.indices,raw_value.options):
                if index not in can_select[participant]:
                    return (False,f"given value '{option.text}' is not selectable by {participant}")
        if min_select is not None:
            if len(raw_value.indices) < min_select:
                return (False,f"you must submit at least {min_select} values")
        if max_select is not None:
            if len(raw_value.indices) > max_select:
                return (False,f"you can only select, at most, {max_select} values")
        return (True,None)
    return validator

default_text_validator:ResponseValidator[Send_Text,Any] = text_validator_maker()