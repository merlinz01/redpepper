import os
import subprocess
import sys

from redpepper.operations import Operation, Result

if sys.platform != "linux":
    raise ImportError("sysctl module only supported on Linux")

SYSCTL_VERSION = int(
    subprocess.run(
        ["dpkg-query", "--showformat", "${Version}\n", "-W", "systemd"],
        capture_output=True,
        text=True,
        check=True,
    )
    .stdout.strip()
    .split(".")[0]
)

# There is already a 99-sysctl.conf, so make this start with "99-x"
SYSCTL_CONF_PATH = "/etc/sysctl.d/99-x-redpepper.conf"
if SYSCTL_VERSION < 207:
    SYSCTL_CONF_PATH = "/etc/sysctl.conf"


class Parameter(Operation):
    def __init__(self, name, value):
        self.name = name
        self.value = str(value)

    def __str__(self):
        return f"sysctl.Parameter({self.name} = {self.value})"

    def test(self, agent):
        if not os.path.exists(SYSCTL_CONF_PATH):
            return False
        with open(SYSCTL_CONF_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=")
                if k.strip() == self.name and v.strip() == self.value:
                    return True
        return False

    def run(self, agent):
        result = Result(self)
        with open(SYSCTL_CONF_PATH, "a") as f:
            f.write(f"\n{self.name} = {self.value}\n")
        result += (
            f'Added sysctl parameter "{self.name} = {self.value}" to {SYSCTL_CONF_PATH}'
        )
        result.changed = True
        p = subprocess.run(["sysctl", "--system"], capture_output=True, text=True)
        result.check_completed_process(p)
        return result
