from typing import Literal

from typing_extensions import TypeVar

type InputName = Literal[
    'Text_Input',
    'Select_Input',
    'Command_Input'
]

InputNameVar = TypeVar('InputNameVar',bound=InputName)