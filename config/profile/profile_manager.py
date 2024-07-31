from contextvars import ContextVar
from typing import Any, override

from config_system_battisti456 import Config_Override

from config.profile.profile import Profile


class Profile_Manager(Config_Override):
    def __init__(self):
        self.profile_var:ContextVar[Profile] = ContextVar('profile_var')
    @property
    def profile(self) -> Profile:
        return self.profile_var.get()
    @profile.setter
    def profile(self,val:Profile):
        self.profile_var.set(val)
    @override
    def defines_property(self, path: str, name: str) -> bool:
        return self.profile.config_override.defines_property(path,name)
    @override
    def get_property(self, path: str, name: str) -> Any:
        return self.profile.config_override.get_property(path,name)
