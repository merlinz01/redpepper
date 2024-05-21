from redpepper.states import State, StateResult


class Show(State):
    _name = "data.Show"

    def __init__(self, name, type="data"):
        self.name = name
        self.type = type

    def run(self, agent):
        result = StateResult(self._name)
        ok, data = agent.request_data(self.type, self.name)
        result.succeeded = ok
        result += data
        return result
