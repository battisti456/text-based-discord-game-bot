import io
from typing import Optional, Sequence

import PIL.ExifTags as ExifTags
import PIL.Image
import PIL.ImageDraw
import requests

from config.game_bases_config import game_bases_config
from game.components.game_interface import Game_Interface
from game.game import Game
from utils.grammar import temp_file_path
from utils.image_search import (
    Image_Search,
    ImageSearchException,
    Pixabay_API,
    Search_Result,
    SearchTerms,
    Unsplash_No_API,
)
from utils.pillow_tools import Persistent_Exif_Image, add_accreditation

ATTRIBUTION_HEIGHT = 10
NUM_RANDOM_SEARCH_TRIES = 10

def embed_search_result(image:PIL.Image.Image,result:Search_Result):
    if image._exif is None:
        image._exif = PIL.Image.Exif()
    exif = image._exif

    if result.artist is not None:
        exif[ExifTags.Base.Artist] = result.artist
    if result.image_type is not None:
        exif[ExifTags.Base.MakerNote] = result.image_type
    #more not implemented


class Image_Search_Base(Game):
    """
    a game base for fetching and managing random images
    """
    def __init__(self,gh:Game_Interface):
        Game.__init__(self,gh)
        if Image_Search_Base not in self.initialized_bases:
            self.initialized_bases.append(Image_Search_Base)
            self.search:Image_Search
            if game_bases_config['random_image_base']['pixabay_token'] is not None:
                self.search = Pixabay_API(game_bases_config['random_image_base']['pixabay_token'])
            else:
                self.search = Unsplash_No_API()
    def random_search(
            self,
            search_terms:Sequence[str],
            size:Optional[tuple[int,int]] = None) -> Search_Result:
        """
        returns a constructed url for finding a random image
        
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
            raise ImageSearchException("No items found.")
        return results[0]
    def get_from_result(self,search_result:Search_Result, auto_accredit:bool = True) -> PIL.Image.Image:
        """
        fetches an image from a url
        """
        url = search_result.raw_image_url
        request = requests.get(url,stream=True)
        if request.status_code == 200:
            image = Persistent_Exif_Image.from_image(PIL.Image.open(io.BytesIO(request.content)))
            image.convert('RGBA')
            embed_search_result(image,search_result)
            if auto_accredit:
                image = add_accreditation(image)
            return image
        else:
            raise ImageSearchException(f"Unable to get image at {url}.")
    def random_image(self,size:Optional[tuple[int,int]] = None,search_terms:list[str] = [],auto_accredit:bool = True) -> PIL.Image.Image:
        """
        fetches a random image based on the given search terms
        
        author: name of an author this image should be by
        
        size: what size the image should be given in
        
        search_terms: what keywords to include in the random search
        """
        tries = 0
        image = None
        while image is None:
            try:
                url = self.random_search(search_terms,size)
                image = self.get_from_result(url,auto_accredit)
            except ImageSearchException:
                ...
            tries += 1
            if tries > NUM_RANDOM_SEARCH_TRIES:
                raise ImageSearchException(f"Unable to randomly for image image using size = {size}, search_terms = {search_terms}, num_tries = {NUM_RANDOM_SEARCH_TRIES}")
        image = image.convert('RGBA')
        return image
    def temp_random_image(self,size:Optional[tuple[int,int]] = None,search_terms:list[str]=[]) -> str:
        image:PIL.Image.Image = self.random_image(size,search_terms)
        path = temp_file_path(".png")
        image.save(path)
        return path
            
        
    
    
        