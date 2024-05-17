import subprocess

from redpepper.states import State


class Run(State):
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
            output = f"$ {self.command} &"
            return output, True
        stdout, stderr = process.communicate(self.stdin)
        if self.capture_stdout:
            output = stdout.decode(self.encoding)
        else:
            output = ""
        if self.capture_stderr:
            output += "\n"
            output += stderr.decode(self.encoding)
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode,
                self.command,
                stdout,
                stderr,
            )
        return output, True


class RunMultiple(State):
    def __init__(self, commands, **kw):
        self.commands = [Run(c, **kw) for c in commands]
        self.kw = kw

    def run(self, agent):
        output = ""
        changed = False
        for cmd in self.commands:
            output += f"Running command: {cmd.command}\n"
            out, chg = cmd.run(agent)
            output += out
            if chg:
                changed = True
        return output, changed
