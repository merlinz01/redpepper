"""Variables and functions for use by the command modules."""

import importlib


class Command:
    """Base class for commands."""

    def run(self, agent) -> tuple[str, bool]:
        """Run the command."""
        raise NotImplementedError

    def test(self, agent) -> bool:
        """Return True if the command's effects already exist."""
        return False

    def ensure(self, agent) -> tuple[str, bool]:
        """Ensure the command is run."""
        if not self.test():
            return self.run()
        return "(no changes needed)", False

    def __str__(self):
        return f"<{self.__class__.__qualname__}>"


def require_python_package(module_name, package_name=None):
    """Ensure a Python package is installed."""
    try:
        mod = importlib.import_module(module_name)
    except ImportError:
        raise
    return mod
