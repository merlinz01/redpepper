import sys

if sys.platform == "linux":
    from redpepper.states.systemd import *
else:
    raise ImportError(f"Unsupported platform for service module: {sys.platform}")
