from typing import Annotated

import ruamel.yaml
import ruamel.yaml.comments
from config_system_battisti456 import Config_Metaclass
from config_system_battisti456.config_item import Ratio
from config_system_battisti456.config_override import Recursive_Mapping_Config_Override

from config.profile import Profile_Manager

LOCAL_CONFIG_FILE = "local_config.yaml"

yaml = ruamel.yaml.YAML()

with open(LOCAL_CONFIG_FILE,'r') as f:
    raw_local_config:ruamel.yaml.comments.CommentedMap = yaml.load(f)


local_override = Recursive_Mapping_Config_Override(raw_local_config)
profile_manager = Profile_Manager()

class Config(metaclass = Config_Metaclass, overrides = (local_override,profile_manager)):
    discord_token:str = ''
    logging_level:str|int = ''
    command_prefix:str = ">> "
    profanity_threshold:Annotated[float,Ratio(level = 1, description='how likely the model must consider text to be profanity before it bans it')]

