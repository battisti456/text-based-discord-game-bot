from typing import Any, Literal

from config_system_battisti456.config_override import Recursive_Mapping_Config_Override
from utils.logging import get_logger

logger = get_logger(__name__)

class Profile():
    def __init__(self, raw_profile_dict:dict[str,Any]):
        self.raw_profile_dict = raw_profile_dict
        self.profile_type:ProfileType = raw_profile_dict['profile_type']
        self.config_override = Recursive_Mapping_Config_Override(self.raw_profile_dict)

type ProfileType = Literal[
    'discord'
]