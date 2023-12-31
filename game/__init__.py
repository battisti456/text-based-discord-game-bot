from typing import TypeVar
from typing import Hashable

DataType = TypeVar('DataType')

type PlayerId = Hashable
type MessageId = Hashable
type ChannelId = Hashable
type InteractionId = Hashable
type PlayerPlacement = list[list[PlayerId]]

type PlayerDict[DataType] = dict[PlayerId,DataType|None]