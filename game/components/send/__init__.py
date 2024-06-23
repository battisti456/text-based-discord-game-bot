import game.components.send.sendable.sendables as sendables
from game.components.send.address import Address
from game.components.send.interaction import Interaction, Interaction_Content
from game.components.send.option import Option
from game.components.send.response import Response
from game.components.send.sendable import Sendable
from game.components.send.sendable.make_sendable import MakeSendableArgs, make_sendable
from game.components.send.sender import Sender
from utils.types import Callback

type InteractionCallback = Callback[Interaction,Response|None]