import io
from typing import Optional, Sequence

import PIL.Image
import PIL.ImageDraw
import requests

from config.game_bases_config import game_bases_config
from game.components.game_interface import Game_Interface
from game.game import Game
from utils.grammer import temp_file_path
from utils.image_search import (
    Image_Search,
    Pixabay_API,
    SearchResult,
    SearchTerms,
    Unsplash_No_API,
)
from utils.pillow_tools import get_font

ATTRIBUTION_HEIGHT = 10


class Random_Image_Base(Game):
    """
    a game base for fetching and managing random images
    """
    def __init__(self,gh:Game_Interface):
        Game.__init__(self,gh)
        if Random_Image_Base not in self.initialized_bases:
            self.initialized_bases.append(Random_Image_Base)
            self.search:Image_Search
            if game_bases_config['random_image_base']['pixabay_token'] is not None:
                self.search = Pixabay_API(game_bases_config['random_image_base']['pixabay_token'])
            else:
                self.search = Unsplash_No_API()
    def random_image_url(
            self,
            search_terms:Sequence[str],
            size:Optional[tuple[int,int]] = None) -> SearchResult:
        """
        returns a contructed url for finding a random image
        
        author: name of an author this image should be by
        
        size: what size the image should be given in
        
        search_terms: what keywords to include in the random search
        """
        s = SearchTerms(
            search_words=list(search_terms),
            sort_option='random',
            width=None if size is None else size[0],
            height=None if size is None else size[1]
        )
        results = self.search(s)
        if len(results) == 0:
            raise Exception("No items found.")
        return results[0]
    def get_image_from_url(self,image_response:SearchResult) -> PIL.Image.Image:
        """
        fetches an image from a url
        """
        url, data = image_response
        request = requests.get(url,stream=True)
        if request.status_code == 200:
            image = PIL.Image.open(io.BytesIO(request.content))
            font = get_font(None,data,{},ATTRIBUTION_HEIGHT,image.width)
            draw = PIL.ImageDraw.ImageDraw(image)
            draw.text((0,image.height-ATTRIBUTION_HEIGHT),data,font=font,anchor='lt')
            return image
        else:
            raise Exception(f"Unable to get image at {url}.")
    def random_image(self,size:Optional[tuple[int,int]] = None,search_terms:list[str] = []) -> PIL.Image.Image:
        """
        fetches a random image based on the given search terms
        
        author: name of an author this image should be by
        
        size: what size the image should be given in
        
        search_terms: what keywords to include in the random search
        """
        url = self.random_image_url(search_terms,size)
        image = self.get_image_from_url(url)
        image = image.convert('RGBA')
        return image
    def temp_random_image(self,size:Optional[tuple[int,int]] = None,search_terms:list[str]=[]) -> str:
        image:PIL.Image.Image = self.random_image(size,search_terms)
        path = temp_file_path(".png")
        image.save(path)
        return path
            
        
    
    
        