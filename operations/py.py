from redpepper.operations import Operation, Result


class Exec(Operation):
    def __init__(self, script, env=None):
        self._script = script
        self.script = compile(script, "<py.Exec>", "exec")
        self.env = globals().copy()
        if env:
            self.env.update(env)

    def __str__(self):
        cmd = self._script
        if "\n" in cmd:
            cmd = cmd.split("\n", 1)[0] + "..."
        if len(cmd) > 50:
            cmd = cmd[:50] + "..."
        return f'py.Exec("{cmd.strip()}")'

    def ensure(self, agent):
        result = Result(self)
        try:
            exec(self.script, self.env, locals())
        except Exception:
            result.exception()
        return result
