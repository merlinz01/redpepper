import os
import subprocess
import sys

from redpepper.operations import Operation, Result

if sys.platform != "linux":
    raise ImportError(f"Unsupported platform for go module: {sys.platform}")


class Installed(Operation):

    def __init__(self, version):
        self.version = version

    def __str__(self):
        return f"go.Installed(version {self.version})"

    def test(self, agent):
        if not os.path.isdir("/usr/local/go"):
            return False
        try:
            p = subprocess.run(
                ["/usr/local/go/bin/go", "version"], text=True, capture_output=True
            )
        except Exception:
            return False
        if not p.stdout.startswith(f"go version go{self.version} "):
            return False
        return True

    def run(self, agent):
        result = Result(self)
        result += "Installing Go..."
        p = subprocess.run(
            [
                "wget",
                f"https://golang.org/dl/go{self.version}.linux-amd64.tar.gz",
                "-O",
                "/tmp/go.tar.gz",
            ],
            text=True,
        )
        if not result.check_completed_process(p).succeeded:
            return result
        p = subprocess.run(
            ["tar", "-C", "/usr/local", "-xzf", "/tmp/go.tar.gz"],
            text=True,
            capture_output=True,
        )
        try:
            os.remove("/tmp/go.tar.gz")
        except OSError:
            result += "Failed to remove temporary download file."
        if not result.check_completed_process(p).succeeded:
            return result
        result += f"Go {self.version} installed to /usr/local/go."
        result.changed = True
        return result
