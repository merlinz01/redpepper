import sys

if sys.platform == "linux":
    from redpepper.operations.systemd import Enabled, Reload, Restart, Running  # noqa
else:
    raise ImportError(f"Unsupported platform for service module: {sys.platform}")
