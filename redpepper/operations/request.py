from redpepper.operations import Operation, Result


class Request(Operation):
    def __init__(self, name, **kwargs):
        self.name = name
        self.kwargs = kwargs

    def __str__(self):
        return f"request.Request({self.name})"

    def run(self, agent):
        result = Result(self)
        data = agent.request(self.name, **self.kwargs)
        result.succeeded = True
        result += str(data)
        return result


class StateRequest(Operation):
    def __init__(self, name, **kwargs):
        self.name = name
        self.kwargs = kwargs

    def __str__(self):
        return f"request.StateRequest({self.name})"

    def run(self, agent):
        result = Result(self)
        data = agent.request("stateDefinition", **self.kwargs)
        result.succeeded = data["succeeded"]
        result.changed = data["changed"]
        result += data["output"]
        return result
