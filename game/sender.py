from game import message

class Sender(object):
    #A callable object used to display a Message to player
    def __init__(self):
        pass
    async def __call__(self,message:message.Message):
        return await self._send(message)
    async def _send(self,message:message.Message):
        pass
class Multiple_Sender(Sender):
    def __init__(self,senders:list[Sender]):
        Sender.__init__(self)
        self.senders = senders
    async def __call__(self, message: message.Message):
        for sender in self.senders:
            await sender(message)
        return await self._send(message)
