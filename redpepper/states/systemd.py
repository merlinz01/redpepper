import subprocess

from redpepper.states import State, StateResult


class Running(State):
    _name = "systemd.Running"

    def __init__(self, name):
        self.name = name

    def test(self, agent):
        cmd = ["systemctl", "is-active", self.name]
        p = subprocess.run(cmd)
        return p.returncode == 0

    def run(self, agent):
        result = StateResult(self._name)
        cmd = ["systemctl", "start", self.name]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if result.check_completed_process(p).succeeded:
            result.changed = True
        return result
