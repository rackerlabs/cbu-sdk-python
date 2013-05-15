class Cleanup(object):
    def __init__(self, agent, cleanup_id):
        self.agent = agent
        self.cleanup_id = cleanup_id

    @property
    def id(self):
        return self.cleanup_id

    @property
    def agent(self):
        return self.agent_id

    @property
    def running(self):
        pass

    @property
    def progress(self):
        pass

    @property
    def state(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def report(self):
        pass
