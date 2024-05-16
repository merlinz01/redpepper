from pepper.states import State, evaluate_condition


class Echo(State):
    def __init__(self, message, reverse=False):
        self.message = message
        self.reverse = reverse

    def run(self, agent):
        message = self.message
        if self.reverse:
            message = message[::-1]
        return message, True
