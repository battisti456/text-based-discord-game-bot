from game import PlayerId
from typing import Callable, Any, Optional

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
        not_is_in:Optional[list[str]] = None
        
) -> ResponseValidator[str]:
    def validator(player:PlayerId,value:Optional[str]) -> Validation:
        if value is None:
            return (False,None)
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
        return (True,None)
    return validator