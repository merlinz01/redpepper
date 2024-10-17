import subprocess
import sys

if sys.platform == "linux":
    DISTROS = {
        "debian": "apt",
        "ubuntu": "apt",
        "linuxmint": "apt",
    }
    d = subprocess.run(
        ["lsb_release", "-is"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    ).stdout.strip()
    package_manager = DISTROS.get(d.lower())
    if package_manager == "apt":
        from redpepper.operations.apt import Installed  # noqa: F401
    else:
        raise ImportError(f"Unknown Linux distro for package module: {d})")
else:
    raise ImportError(f"Unsupported platform for package module: {sys.platform}")
