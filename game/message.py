from game import PlayerId, MessageId, ChannelId

from math import ceil

from typing import Optional

class Message(object):
    def __init__(
            self,content:Optional[str] = None,attach_paths:list[str] = [],
            channel_id:Optional[ChannelId] = None,message_id:Optional[MessageId] = None,
            keep_id_on_copy:bool = False, players_who_can_see:Optional[list[PlayerId]] = None):
        self.content = content
        self.attach_paths = attach_paths
        self.channel_id = channel_id
        self.message_id = message_id
        self.keep_id_on_copy = keep_id_on_copy
        self.players_who_can_see = players_who_can_see
    def copy(self) -> 'Message':
        if self.keep_id_on_copy:
            message_id = self.message_id
        else:
            message_id = None
        return Message(self.content,self.attach_paths,self.channel_id,message_id,self.keep_id_on_copy,self.players_who_can_see)
    def is_sent(self) -> bool:
        return not self.message_id is None
    def split(self,deliminator:Optional[str] = None,length:Optional[int] = None,add_join:str = "") -> list['Message']:
        if self.content is None:
            return [self]
        partials:list[str] = []
        if not deliminator is None:
            partials = self.content.split(deliminator)
        else:
            partials = [self.content]
        if not length is None:
            length_exceeding_indexes:list[int] = []
            for i in range(len(partials)-1,-1,-1):
                if len(partials[i]) > length:
                    length_exceeding_indexes.append(i)
            for i in length_exceeding_indexes:
                sub_partials = []
                num_splits = ceil(len(partials[i])/length)
                for j in range(num_splits,-1,-1):
                    sub_partials.append(partials[i][j*length:(j+1)*length])
                partials.pop(i)
                for sub_partial in sub_partials:
                    partials.insert(i,sub_partial)
        to_return = []
        for partial in partials:
            message = self.copy()
            if len(to_return) != len(partials) - 1:
                message.content = f"{partial}{add_join}"
            else:
                message.content = partial
            to_return.append(message)
        return to_return


            
                
