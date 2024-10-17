import os
import pwd
import subprocess

from redpepper.operations import Operation, Result


class Run(Operation):
    def __init__(
        self,
        command,
        user=None,
        group=None,
        shell=True,
        cwd=None,
        stdin=None,
        wait=True,
        env=None,
        capture_stdout=True,
        capture_stderr=True,
        encoding="utf-8",
    ):
        self.command = command
        self.user = user
        self.group = group
        self.shell = shell
        self.cwd = cwd
        if stdin is not None:
            self.stdin = stdin.encode(encoding)
        else:
            self.stdin = None
        self.wait = wait
        if env:
            if not isinstance(env, dict):
                raise TypeError("env must be a mapping of environment variables")
            self.env = {}
            for k, v in env.items():
                if isinstance(v, (str, int, float, bool)):
                    self.env[k] = str(v)
                else:
                    raise TypeError(
                        f"Environment variable {k} has invalid type {type(v).__name__}"
                    )
        else:
            self.env = None
        self.capture_stdout = capture_stdout
        self.capture_stderr = capture_stderr
        self.encoding = encoding
        if not wait and (capture_stdout or capture_stderr):
            raise ValueError(
                "Cannot capture output if not waiting for command to finish"
            )

    def __str__(self):
        return f'Run("{self.command}{"" if self.wait else " &"}"{" as " + self.user if self.user else ""})'

    def run(self, agent):
        result = Result(self)
        kw = {}
        kw["env"] = os.environ.copy()
        if self.user:
            kw["user"] = self.user
            kw["env"]["HOME"] = pwd.getpwnam(self.user).pw_dir
        if self.group:
            kw["group"] = self.group
        elif self.user:
            kw["group"] = pwd.getpwnam(self.user).pw_gid
        if self.shell:
            kw["shell"] = True
        if self.cwd:
            kw["cwd"] = self.cwd
        if self.env is not None:
            kw["env"].update(self.env)
        if self.stdin is not None:
            kw["stdin"] = subprocess.PIPE
        if self.capture_stdout:
            kw["stdout"] = subprocess.PIPE
        if self.capture_stderr:
            kw["stderr"] = subprocess.PIPE
        process: subprocess.Popen[bytes] = subprocess.Popen(self.command, **kw)  # type: ignore
        if not self.wait:
            result += f"$ {self.command} &"
            return result
        stdout, stderr = process.communicate(self.stdin)
        if self.capture_stdout and stdout:
            result += stdout.decode(self.encoding, errors="replace").rstrip()
        if self.capture_stderr and stderr:
            result += (
                "Stderr:\n" + stderr.decode(self.encoding, errors="replace").rstrip()
            )
        if process.returncode != 0:
            result.fail(f"Command failed with return code {process.returncode}")
        result.changed = True
        return result


class RunMultiple(Operation):
    def __init__(self, commands, **kw):
        self.commands = [Run(c, **kw) for c in commands]
        self.kw = kw

    def __str__(self):
        return f"RunMultiple({len(self.commands)} commands)"

    def run(self, agent):
        result = Result(self)
        for cmd in self.commands:
            result += f"Running {cmd}:"
            if not result.update(cmd.run(agent)).succeeded:
                return result
        return result
