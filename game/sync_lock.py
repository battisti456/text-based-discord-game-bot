
class Sync_Lock(object):
    def __init__(self):
        self.ready_to_end_execution = False
    def check_ready_to_end(self):
        pass
    def __bool__(self) -> bool:
        self.check_ready_to_end()
        return self.ready_to_end_execution
    def end_execution(self):
        self.ready_to_end_execution = True
    async def update(self):
        pass
