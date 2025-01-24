import uuid
from typing import Iterable

from utils.types import Number
from utils.word_tools import Sentence

from smart_text import TextLike

def nice_sentence(sentence:Sentence) -> str:
    return (" ".join(sentence)).replace('_',' ').capitalize()
def wordify_iterable(values:Iterable[TextLike],operator:TextLike = 'and',comma:TextLike = ",") -> TextLike:
    """
    takes an iterable of values, turns it into a list ad formats it into a ___, ___, and __ string;
    if values is of length one, it returns the value unchanged;
    if values is of length two, returns ___ and ___ (no comma)

    operator: replaces 'and', eg 'or'

    comma: replaces ',' eg. ';'
    """
    to_return:TextLike = ""
    if not isinstance(values,list):
        values = list(values)
    if len(values) == 0:
        return ""
    elif len(values) == 1:
        return values[0]
    elif len(values) == 2:
        return values[0] + ' ' + operator + ' ' + values[1]
    for i in range(len(values)):
        if i != 0:
            if i == len(values) -1:#is last
                to_return += comma + ' ' + operator + ' '
            else:
                to_return += comma + ' '
        if isinstance(values[i],str):
            to_return += values[i]
        else:
            to_return += str(values[i])
    return to_return
def ordinate(num:Number|str) -> str:
    """
    takes a number and returns a string with the appropriate 'st', 'nd', 'rd', or 'th' appended to that number
    """
    num = str(num)
    ordinal = ""
    if num[-1] == '1':
        ordinal = "st"
    elif num[-1] == '2':
        ordinal = "nd"
    elif num[-1] == '3':
        ordinal = "rd"
    else:
        ordinal = "th"
    if num in (11,12,13):
        ordinal = 'th'
    return num + ordinal
TEMP_PATH = "temp"
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = SECONDS_PER_MINUTE*60
SECONDS_PER_DAY = SECONDS_PER_HOUR*24
def nice_time(time:int) -> str:
    """
    converts a time in seconds into a more readable approximation
    not finished
    """
    num_days = int(time/SECONDS_PER_DAY)
    time = time%SECONDS_PER_DAY
    num_hours = int(time/SECONDS_PER_HOUR)
    time = time%SECONDS_PER_HOUR
    num_minutes = int(time/SECONDS_PER_MINUTE)
    num_seconds = time%SECONDS_PER_MINUTE
    strings:list[str] = []
    if num_days:
        strings.append(f"{num_days} day{s(num_days)}")
    if num_hours:
        strings.append(f"{num_hours} hour{s(num_hours)}")
    if num_minutes:
        strings.append(f"{num_minutes} minute{s(num_minutes)}")
    if num_seconds:
        strings.append(f"{num_seconds} second{s(num_seconds)}")
    return wordify_iterable(strings)
def s(num:Number) -> str:
    return '' if num == 1 else 's'
def temp_file_path(file_type:str) -> str:
    """
    returns a theoretical random file path with the given file_type;
    it doesn't actually check that the file doesn't already exist
    """
    return f"{TEMP_PATH}//{uuid.uuid4()}{file_type}"
def moneyfy(value:Number):
    to_return = ""
    if value < 0:
        to_return += "-"
    to_return += "$" + str(abs(value))
    return to_return
def percentify(value:float,decimal_points:int = 2):
    percent:float = value*100
    nums = int(percent)
    decimals = int((percent-nums)*10**decimal_points)
    if decimal_points > 0 and decimals != 0:
        return f"{nums}.{decimals}%"
    else:
        return f"{nums}%"

def append_s(text:TextLike) -> TextLike:
    if str(text)[-1] == 's':
        return text
    else:
        return text + 's'