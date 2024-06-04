import os
import subprocess
import sys

from redpepper.states import State, StateResult


class Installed(State):
    _name = "go.Installed"

    def __init__(self, version):
        self.version = version
        if sys.platform != "linux":
            raise NotImplementedError("Only Linux is supported")

    def test(self, agent):
        if not os.path.isdir("/usr/local/go"):
            return False
        try:
            output = subprocess.check_output(
                ["/usr/local/go/bin/go", "version"], text=True
            )
        except Exception:
            return False
        if not output.startswith(f"go version go{self.version} "):
            return False
        return True

    def run(self, agent):
        result = StateResult(self._name)
        result += "Installing Go..."
        rc, output = subprocess.getstatusoutput(
            [
                "wget",
                f"https://golang.org/dl/go{self.version}.linux-amd64.tar.gz",
                "-O",
                "/tmp/go.tar.gz",
            ],
            text=True,
        )
        if rc != 0:
            result.fail(f"Failed to download Go:\n{output}")
            return result
        rc, output = subprocess.getstatusoutput(
            ["tar", "-C", "/usr/local", "-xzf", "/tmp/go.tar.gz"], text=True
        )
        try:
            os.remove("/tmp/go.tar.gz")
        except OSError:
            result += "Failed to remove temporary download file."
            pass
        if rc != 0:
            result.fail(f"Failed to extract Go:\n{output}")
            return result
        result += f"Go {self.version} installed to /usr/local/go."
        return result
