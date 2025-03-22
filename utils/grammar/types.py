from typing import Literal, get_args

type Lower_Case_Letter = Literal['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']

LOWER_CASE_LETTERS:tuple[Lower_Case_Letter] = get_args(Lower_Case_Letter)