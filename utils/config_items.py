from typing import Unpack, Any

from config_system_battisti456.config_item import Config_Item, ConfigArgs
from color_tools_battisti456 import color_to_tuple_rgb, TupleRGB, TupleRGBA

class ColorConfigItem(Config_Item):
    def __init__(self,**kwargs:Unpack[ConfigArgs]):
        add_text:str = "a color defined by (R,G,B), (R,G,B,A), '#rrggbb', '#rrggbbaa' or 'color_name'"
        if 'description' in kwargs:
            add_text += f"; {kwargs['description']}"
        def checker(value:Any) -> bool:
            try:
                _: TupleRGB|TupleRGBA = color_to_tuple_rgb(value)
                return True
            except Exception:
                return False
        super().__init__(add_text,checker,kwargs['level'])