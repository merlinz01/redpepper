import logging
import subprocess

from redpepper.states import State

logger = logging.getLogger(__name__)


class Installed(State):
    def __init__(
        self,
        name,
    ):
        self.name = name

    def test(self, agent):
        cmd = [
            "dpkg-query",
            "--showformat",
            "${Package}\t${Version}\t${db:Status-Status}\n",
            "-W",
            self.name,
        ]
        logger.debug(
            "Testing if apt package %s is installed with command %r", self.name, cmd
        )
        p = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if p.returncode == 1:
            logger.debug("dpkg-query returned 1")
            return False
        elif p.returncode == 0:
            logger.debug("dpkg-query returned 0, output: %r", p.stdout)
            for line in p.stdout.splitlines():
                package, version, status = line.split("\t")
                if package != self.name:
                    continue
                return status == "installed"
            return False
        else:
            logger.error("dpkg-query failed with return code %s", p.returncode)
            raise subprocess.CalledProcessError(p.returncode, cmd, p.stdout, p.stderr)

    def run(self, agent):
        cmd = ["apt-get", "install", "-q", "-y", self.name]
        output = subprocess.check_output(cmd, text=True)
        return output, True


class UnattendedUpgrade(State):
    def __init__(self):
        pass

    def run(self, agent):
        output, changed = Installed("unattended-upgrade").ensure(agent)
        if changed:
            output = f"Installing unattended-upgrades:\n{output}"
        else:
            output = ""
        cmd_output, rc = subprocess.getstatusoutput(["unattended-upgrades"], text=True)
        if rc != 0:
            raise subprocess.CalledProcessError(rc, cmd_output)
        if cmd_output:
            changed = True
        output += cmd_output
        return output, changed
