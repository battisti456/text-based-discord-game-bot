from game import PlayerId
from typing import Callable, Any, Optional

from config.config import config
from profanity_check import predict_prob

type Validation = tuple[bool,str|None]
type ResponseValidator[DataType] = Callable[[PlayerId,DataType|None],Validation]

not_none:ResponseValidator[Any] = lambda player, data: (not data is None,None)

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
        is_stricly_composed_of:Optional[str] = None,
        check_lower_case:bool = False,
        min_num_words:Optional[int] = None,
        max_num_words:Optional[int] = None
        
) -> ResponseValidator[str]:
    """creates a response validator for str's matching given validation, and with feedback given on problems with the input"""
    def validator(player:PlayerId,value:Optional[str]) -> Validation:
        if value is None:
            return (False,None)
        if predict_prob([value])[0] >= config['profanity_threshold']:
            return (False,"given value set off the profanity filter")
        if check_lower_case:
            value = value.lower()
        if not is_substr_of is None:
            if not value in is_substr_of:
                return (False,f"given value '{value}' not in '{is_substr_of}'")
        if not is_supstr_of is None:
            if not is_supstr_of in value:
                return (False,f"'{is_supstr_of}' not in given value '{value}'")
        if not max_length is None:
            if len(value) > max_length:
                return (False,f"given value '{value}' of length {len(value)} exceeds the maximum length of {max_length}")
        if not min_length is None:
            if len(value) < min_length:
                return (False,f"given value '{value}' of length {len(value)} is below the minimum length of {min_length}")
        if not is_alpha is None:
            if not value.isalpha():
                return (False,f"given value '{value}' contains non-alphabetical characters")
        if not is_alnum is None:
            if not value.isalnum():
                return (False,f"given value '{value}' contains characters which are neither alphabetic or numeric")
        if not is_decimal is None:
            if not value.isdecimal():
                return (False,f"given value '{value}' contains non-decimal characters")
        if not is_digit is None:
            if not value.isdigit():
                return (False,f"given value '{value}' is not a digit")
        if not is_in is None:
            if not value in is_in:
                return (False,f"given value '{value}' not in acceptable values")
        if not not_is_in is None:
            if value in not_is_in:
                return (False,f"given value '{value}' is a banned value")
        if not is_composed_of is None:
            if not all(letter in is_composed_of for letter in value):
                return (False,f"given value '{value}' contains characters not found in '{is_composed_of}'")
        if not is_stricly_composed_of is None:
            list_letters = list(is_stricly_composed_of)
            for letter in value:
                if letter in list_letters:
                    list_letters.remove(letter)
                else:
                    return (False,f"given value '{value}' contains more characters than are found in '{is_stricly_composed_of}'")
        num_words =  len(value.split())
        if not min_num_words is None:
            if num_words < min_num_words:
                return (False,f"given value '{value}' contains {num_words} word(s) which is less than the minimum of {min_num_words} words")
        if not max_num_words is None:
            if num_words > max_num_words:
                return (False,f"given value '{value}' contains {num_words} word(s) which is more than the maximum of {min_num_words} words")
        return (True,None)
    return validator
default_text_validator:ResponseValidator = text_validator_maker()