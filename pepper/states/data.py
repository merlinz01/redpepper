from pepper.states import State


class Show(State):
    def __init__(self, data, dtype="data"):
        self.data = data
        self.dtype = dtype

    def run(self, agent):
        ok, data = agent.request_data(self.dtype, self.data)
        if not ok:
            return f"Failed to retrieve data {self.data}: {data}", False
        return f"Data {self.data} = {data!r}", False
