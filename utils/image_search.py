import dataclasses
import io
import json
from random import shuffle
from typing import Literal, Optional, override

import requests

type SearchResult = tuple[str,str]
"url,accreditation"
type ImageType = Literal['photo','illustration','vector']
type SortOption = Literal['popular','latest','random']

class ImageSearchException(Exception):
    ...

@dataclasses.dataclass
class SearchTerms():
    search_words:Optional[list[str]] = None
    image_type:Optional[ImageType] = None
    vertical:Optional[bool] = None
    height:Optional[int] = None
    width:Optional[int] = None
    safesearch:bool = True
    sort_option:Optional[SortOption] = None
    max_hits:int = 20

@dataclasses.dataclass
class Image_Search():
    def __call__(self,s:SearchTerms) -> list[SearchResult]:
        ...


@dataclasses.dataclass
class Pixabay_API(Image_Search):
    BASE_URL = "https://pixabay.com/api"
    MAX_PAGE_RESULTS = 200
    token:str
    @override
    def __call__(self, s: SearchTerms, _page:int = 1) -> list[SearchResult]:
        parameters:list[str] = []
        parameters.append(f"key={self.token}")
        if s.search_words is not None:
            parameters.append(f"q={'+'.join(s.search_words)}")
        if s.image_type is not None:
            parameters.append(f"image_type={s.image_type}")
        if s.vertical is not None:
            if s.vertical:
                parameters.append("orientation=vertical")
            else:
                parameters.append("orientation=horizontal")
        if s.height is not None:
            parameters.append(f"min_height={s.height}")
        if s.width is not None:
            parameters.append(f"min_width={s.width}")
        if s.safesearch:
            parameters.append("safesearch=true")
        if s.sort_option == 'latest':#popular by default, no random
            parameters.append("order=latest")
        parameters.append(f"page={_page}")
        if s.sort_option == 'random' or s.max_hits > Pixabay_API.MAX_PAGE_RESULTS:
            parameters.append(f"per_page={Pixabay_API.MAX_PAGE_RESULTS}")#get max number of hits for random
        else:
            parameters.append(f"per_page={s.max_hits}")
        
        api_url = f"{Pixabay_API.BASE_URL}/?{'&'.join(parameters)}"
        request = requests.get(api_url,stream=True)
        data = json.load(io.BytesIO(request.content))
        to_return = list(
            (
                hit['largeImageURL'],
                f"Sourced from {hit['pageURL']}"
            )
            for hit in data['hits'])
        if len(to_return) == Pixabay_API.MAX_PAGE_RESULTS and s.max_hits > Pixabay_API.MAX_PAGE_RESULTS:
            ms = dataclasses.replace(s)
            ms.max_hits = Pixabay_API.MAX_PAGE_RESULTS
            if s.sort_option == 'random':
                ms.sort_option = None
            while len(to_return) < s.max_hits:
                was_returned = self(ms,_page + 1)
                to_return += was_returned
                if len(was_returned) < Pixabay_API.MAX_PAGE_RESULTS:
                    break
        if s.sort_option == 'random':
            shuffle(to_return)
        to_return = to_return[:s.max_hits]
        return to_return

class Unsplash_No_API(Image_Search):
    BASE_URL = "https://source.unsplash.com/random"
    @override
    def __call__(self, s: SearchTerms) -> list[SearchResult]:
        url_end:str = ""
        if s.width is not None and s.height is not None:
            url_end += f"/{s.width}x{s.height}"
        if s.search_words is not None:
            url_end += f"/?{','.join(s.search_words)}"
        return [(f"{Unsplash_No_API.BASE_URL}{url_end}","")]