from redpepper.states import State, StateResult


class Show(State):
    _name = "data.Show"

    def __init__(self, data, dtype="data"):
        self.data = data
        self.dtype = dtype

    def run(self, agent):
        result = StateResult(self._name)
        ok, data = agent.request_data(self.dtype, self.data)
        result.succeeded = ok
        result += data
        return result
