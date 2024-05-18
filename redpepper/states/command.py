import subprocess

from redpepper.states import State, StateResult


class Run(State):
    _name = "command.Run"

    def __init__(
        self,
        command,
        user=None,
        group=None,
        shell=True,
        stdin=None,
        wait=True,
        capture_stdout=True,
        capture_stderr=True,
        encoding="utf-8",
    ):
        self.command = command
        self.user = user
        self.group = group
        self.shell = shell
        if stdin is not None:
            self.stdin = stdin.encode(encoding)
        else:
            self.stdin = None
        self.wait = wait
        self.capture_stdout = capture_stdout
        self.capture_stderr = capture_stderr
        self.encoding = encoding
        if not wait and (capture_stdout or capture_stderr):
            raise ValueError(
                "Cannot capture output if not waiting for command to finish"
            )

    def run(self, agent):
        result = StateResult(self._name)
        kw = {}
        if self.user:
            kw["user"] = self.user
        if self.group:
            kw["group"] = self.group
        if self.shell:
            kw["shell"] = True
        if self.stdin is not None:
            kw["stdin"] = subprocess.PIPE
        if self.capture_stdout:
            kw["stdout"] = subprocess.PIPE
        if self.capture_stderr:
            kw["stderr"] = subprocess.PIPE
        process = subprocess.Popen(self.command, **kw)
        if not self.wait:
            result += f"$ {self.command} &"
            return result
        stdout, stderr = process.communicate(self.stdin)
        if self.capture_stdout:
            result += stdout.decode(self.encoding, errors="replace")
        if self.capture_stderr:
            result += "\nStderr:" + stderr.decode(self.encoding, errors="replace")
        if process.returncode != 0:
            result.fail(f"Command failed with return code {process.returncode}")
        return result


class RunMultiple(State):
    _name = "command.RunMultiple"

    def __init__(self, commands, **kw):
        self.commands = [Run(c, **kw) for c in commands]
        self.kw = kw

    def run(self, agent):
        result = StateResult(self._name)
        for cmd in self.commands:
            result += f"$ {cmd.command}"
            if not result.update(cmd.run(agent)).succeeded:
                return result
        return result
