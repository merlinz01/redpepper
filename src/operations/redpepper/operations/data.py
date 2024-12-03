from redpepper.operations import Operation, Result


class Show(Operation):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"data.Show({self.name})"

    async def run(self, agent):
        result = Result(self)
        data = await agent.conn.rpc.call("custom", "data", name=self.name)
        result.succeeded = True
        result += data
        return result
