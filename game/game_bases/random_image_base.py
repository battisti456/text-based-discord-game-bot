from game.game import Game
from game.game_interface import Game_Interface
from typing import TypedDict

import PIL.Image
import requests
import io

BASE_URL = "https://source.unsplash.com"


class Random_Image_Base(Game):
    def __init__(self,gh:Game_Interface):
        Game.__init__(self,gh)
        if not Random_Image_Base in self.initialized_bases:
            self.initialized_bases.append(Random_Image_Base)
    def random_image_url(self,author:str = None, size:tuple[int,int] = None,search_terms:list[str] = None) -> str:
        source_text = "/random"
        if not author is None:
            source_text = f"/user/{author}"
        size_text = ""
        if not size is None:
            size_text = f"/{size[0]}x{size[1]}"
        search_text = ""
        if not search_terms is None:
            search_text = f"/?{','.join(search_terms)}"
        return f"{BASE_URL}{source_text}{size_text}{search_text}"
    def get_image_from_url(self,url:str) -> PIL.Image.Image:
        request = requests.get(url,stream=True)
        if request.status_code == 200:
            return PIL.Image.open(io.BytesIO(request.content))
        else:
            self.logger.error(f"Image at '{url}' could not be accessed.")
            return None
    def random_image(self,author:str = None, size:tuple[int,int] = None,search_terms:list[str] = None) -> PIL.Image.Image:
        url = self.random_image_url(author,size,search_terms)
        image = self.get_image_from_url(url)
        if not image is None:
            return image
        else:
            return self.random_image(author,size,search_terms)
            
        
    
    
        