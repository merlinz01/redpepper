import sys

from pepper.commands import require_python_package

if sys.platform == "linux":
    distro = require_python_package("distro")
    d = distro.id()
    like = distro.like()
    if "debian" in like:
        from pepper.commands.apt import *
    else:
        raise ImportError(
            f"Unsupported Linux distro for package module: {d} (like {like})"
        )
else:
    raise ImportError(f"Unsupported platform for package module: {sys.platform}")
