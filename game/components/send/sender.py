from typing import TYPE_CHECKING, Generic, Hashable

from typing_extensions import TypeVar

from utils.logging import get_logger
from game.components.send.address import Address

if TYPE_CHECKING:
    from game.components.send.sendable import Sendable

logger = get_logger(__name__)

SenderSendAddress = TypeVar('SenderSendAddress',bound=Address)

class Sender(Generic[SenderSendAddress]):
    """a callable object whose responsibility it is to interpret Messages and display them"""
    def __init__(self):
        pass
    async def __call__(self,sendable:'Sendable',address:SenderSendAddress|None = None) -> SenderSendAddress:
        """display Message object for the players according to it's parameters"""
        return await self._send(sendable,address)
    async def _send(self,sendable:'Sendable',address:SenderSendAddress|None = None) -> SenderSendAddress:
        """lowest level definition of the default Sender's sending capabilities"""
        logger.info(f"Sent {sendable} at {address}.")
        return await self.generate_address()
    async def generate_address(self,*args:Hashable) -> SenderSendAddress:
        raise NotImplementedError()
