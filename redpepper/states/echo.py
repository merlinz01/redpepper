from redpepper.states import State, StateResult


class Echo(State):
    _name = "echo.Echo"

    def __init__(self, message, reverse=False):
        self.message = message
        self.reverse = reverse

    def run(self, agent):
        result = StateResult(self._name)
        message = self.message
        if self.reverse:
            message = message[::-1]
        result += message
        return result
