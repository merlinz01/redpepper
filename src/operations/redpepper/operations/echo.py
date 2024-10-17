from redpepper.operations import Operation, Result


class Echo(Operation):
    def __init__(self, message, reverse=False):
        self.message = message
        self.reverse = reverse

    def __str__(self):
        return f'echo.Echo("{self.message}"{" reverse" if self.reverse else ""})'

    def run(self, agent):
        result = Result(self)
        message = self.message
        if self.reverse:
            message = message[::-1]
        result += message
        return result
