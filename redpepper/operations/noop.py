from redpepper.operations import Operation, Result


class Noop(Operation):
    def __init__(self):
        pass

    def __str__(self):
        return "no-op"

    def ensure(self, agent):
        result = Result(self)
        result.succeeded = True
        return result
