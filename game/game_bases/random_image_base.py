import game

from typing import TypedDict

from unsplash.api import Api
from unsplash.auth import Auth

class RIBConfig(TypedDict):
    access_key:str
    secret_key:str
    app_id:int
    uri:str

class Random_Image_Base(game.Game):
    def __init__(self,gh:game.GH):
        game.Game.__init__(self,gh)
        if not Random_Image_Base in self.initialized_bases:
            self.initialized_bases.append(Random_Image_Base)
            self.rib_config:RIBConfig = self.gh.config['game_configs']['random_image_base']
            self.setup_rib()
    def setup_rib(self):
        Auth()
        self.auth = Auth(
            self.rib_config['app_id'],
            self.rib_config['secret_key'],
            self.rib_config['uri'])
        self.api = Api(self.auth)
    
    
        