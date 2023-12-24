from game import message

class Sender(object):
    def __init__(self):
        pass
    async def __call__(self,message:message.Message):
        return await self._send(message)
    async def _send(self,message:message.Message):
        pass
