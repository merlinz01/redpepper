import logging
import subprocess

from redpepper.states import State, StateResult

logger = logging.getLogger(__name__)


class Installed(State):
    _name = "apt.Installed"

    def __init__(self, name):
        self.name = name

    def test(self, agent):
        cmd = [
            "dpkg-query",
            "--showformat",
            "${Package}\t${db:Status-Status}\n",
            "-W",
            self.name,
        ]
        logger.debug(
            "Testing if apt package %s is installed with command %r", self.name, cmd
        )
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode == 1:
            logger.debug("dpkg-query returned 1")
            return False
        elif p.returncode == 0:
            logger.debug("dpkg-query returned 0, output: %r", p.stdout)
            for line in p.stdout.splitlines():
                package, status = line.split("\t")
                if package != self.name:
                    continue
                return status == "installed"
            return False
        else:
            logger.error("dpkg-query failed with return code %s", p.returncode)
            raise subprocess.CalledProcessError(p.returncode, cmd, p.stdout, p.stderr)

    def run(self, agent):
        result = StateResult(self._name)
        cmd = ["apt-get", "-q", "-y", "install", self.name]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if result.check_completed_process(p).succeeded:
            result.changed = "Setting up" in p.stdout
        return result


class UnattendedUpgrade(State):
    _name = "apt.UnattendedUpgrade"

    def __init__(self):
        pass

    def run(self, agent):
        result = StateResult(self._name)
        if not result.update(Installed("unattended-upgrade").ensure(agent)).succeeded:
            return result
        p = subprocess.run(["unattended-upgrades"], capture_output=True, text=True)
        if result.check_completed_process(p).succeeded:
            result.changed = p.stdout != ""
        return result
