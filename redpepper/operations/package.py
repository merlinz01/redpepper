import sys

from redpepper.operations import require_python_package

if sys.platform == "linux":
    distro = require_python_package("distro")
    d = distro.id()
    like = distro.like()
    if d == "debian" or "debian" in like:
        from redpepper.operations.apt import *
    else:
        raise ImportError(
            f"Unsupported Linux distro for package module: {d} (like {like})"
        )
else:
    raise ImportError(f"Unsupported platform for package module: {sys.platform}")
