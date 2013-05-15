from python_rcbu.client.agent import Agent as UserAgent

class Agent(UserAgent):
    def __init__(self, agent_id, password):
        self.agent_id = agent_id
        self.password = password

    @property
    def logs(self):
        pass

    @property
    def configuration(self):
        pass

    @property
    def password(self):
        pass

    def get_log(self, log_id):
        pass
