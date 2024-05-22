import io
from typing import Optional, NewType, Callable, Sequence

import PIL.Image
import requests

from game.components.game_interface import Game_Interface
from game.game import Game
from utils.grammer import temp_file_path

BASE_URL = "https://source.unsplash.com"#seems to be broken, look into this: https://pixabay.com/api/docs/

ImageUrl = NewType("ImageUrl",str)
type ImageFinder = Callable[[Sequence[str],tuple[int,int]],ImageUrl]

def source_unsplash_image_finder(search_terms:Sequence[str],size:tuple[int,int]) -> ImageUrl:
    #the api seems to no longer function
    source_text = "/random"
    size_text = ""
    if size is not None:
        size_text = f"/{size[0]}x{size[1]}"
    search_text = ""
    if search_terms is not None:
        search_text = f"/?{','.join(search_terms)}"
    return f"https://source.unsplash.com{source_text}{size_text}{search_text}"#type:ignore

class Random_Image_Base(Game):
    """
    a game base for fetching and managing random images
    """
    def __init__(self,gh:Game_Interface):
        Game.__init__(self,gh)
        if Random_Image_Base not in self.initialized_bases:
            self.initialized_bases.append(Random_Image_Base)
    def random_image_url(
            self,
            author:Optional[str] = None, 
            size:Optional[tuple[int,int]] = None,
            search_terms:Optional[list[str]] = None) -> str:
        """
        returns a contructed url for finding a random image
        
        author: name of an author this image should be by
        
        size: what size the image should be given in
        
        search_terms: what keywords to include in the random search
        """
        source_text = "/random"
        if author is not None:
            source_text = f"/user/{author}"
        size_text = ""
        if size is not None:
            size_text = f"/{size[0]}x{size[1]}"
        search_text = ""
        if search_terms is not None:
            search_text = f"/?{','.join(search_terms)}"
        return f"{BASE_URL}{source_text}{size_text}{search_text}"
    def get_image_from_url(self,url:str) -> PIL.Image.Image:
        """
        fetches an image from a url
        """
        request = requests.get(url,stream=True)
        if request.status_code == 200:
            return PIL.Image.open(io.BytesIO(request.content))
        else:
            raise Exception(f"Unable to get image at {url}.")
    def random_image(self,author:Optional[str] = None, size:Optional[tuple[int,int]] = None,search_terms:Optional[list[str]] = None) -> PIL.Image.Image:
        """
        fetches a random image based on the given search terms
        
        author: name of an author this image should be by
        
        size: what size the image should be given in
        
        search_terms: what keywords to include in the random search
        """
        url = self.random_image_url(author,size,search_terms)
        image = self.get_image_from_url(url)
        if image is not None:
            return image
        else:
            return self.random_image(author,size,search_terms)
    def temp_random_image(self,author:Optional[str] = None, size:Optional[tuple[int,int]] = None,search_terms:Optional[list[str]]=None) -> str:
        image:PIL.Image.Image = self.random_image(author,size,search_terms)
        path = temp_file_path(".png")
        image.save(path)
        return path
            
        
    
    
        