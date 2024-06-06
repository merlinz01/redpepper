from redpepper.operations import Operation, Result


class Show(Operation):

    def __init__(self, name, type="data"):
        self.name = name
        self.type = type

    def __str__(self):
        return f'data.Show({self.type} "{self.name}")'

    def run(self, agent):
        result = Result(self)
        ok, data = agent.request_data(self.type, self.name)
        result.succeeded = ok
        result += data
        return result
