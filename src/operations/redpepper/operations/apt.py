import logging
import subprocess

from redpepper.operations import Operation, Result

logger = logging.getLogger(__name__)


class Installed(Operation):
    _no_changes_text = "The package is already installed."

    def __init__(self, name, env={}):
        self.name = name
        if not isinstance(env, dict):
            raise ValueError("env must be a mapping")
        self.env = env

    def __str__(self):
        return f"apt.Installed({self.name})"

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
        result = Result(self)
        cmd = [
            "apt-get",
            "-q",  # quiet
            "-y",  # assume yes
            "-o",
            "DPkg::Options::=--force-confold",  # keep old config files
            "-o",
            "DPkg::Options::=--force-confdef",  # keep new config files
            "install",  # install package
            self.name,  # package name
        ]
        env = self.env
        env["DEBIAN_FRONTEND"] = "noninteractive"  # don't ask questions
        env["APT_LISTCHANGES_FRONTEND"] = "none"  # don't show changelogs
        env["APT_LISTBUGS_FRONTEND"] = "none"  # don't show bug reports
        env["UCF_FORCE_CONFFOLD"] = "1"  # keep old config files
        p = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.check_completed_process(p).succeeded:
            result.changed = "Setting up" in p.stdout
        return result


class UnattendedUpgrade(Operation):
    def __str__(self):
        return "apt.UnattendedUpgrade()"

    def run(self, agent):
        result = Result(self)
        if not result.update(Installed("unattended-upgrades").ensure(agent)).succeeded:
            return result
        p = subprocess.run(["unattended-upgrades"], capture_output=True, text=True)
        if result.check_completed_process(p).succeeded:
            result.changed = result.changed or p.stdout != ""
        return result
