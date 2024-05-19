from typing import Optional, override


class GameBotException(Exception):
    ...

class GameException(GameBotException):
    ...

class GameEndException(GameException):
    def __init__(self,message:Optional[str] = None):
        """
        message: ...caused by ________.
        """
        if message is not None:
            super().__init__(message)
        else:
            super().__init__()
        self._explanation:str = "an unspecified reason"
    @property
    def explanation(self) -> str:
        start:str = "The game has ended due to "
        end:str = "."
        if self.args:
            end = f" caused by {self.args[0]}."
        return f"{start}{self._explanation}{end}"
    @override
    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.explanation}"

class GameEndInsufficientPlayers(GameEndException):
    def __init__(self,message:Optional[str] = None):
        """
        message: ...caused by ________.
        """
        GameEndException.__init__(self,message)
        self._explanation:str = "a lack of sufficient remaining players"

class GameEndInsufficientTeams(GameEndInsufficientPlayers):
    ...