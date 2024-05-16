"""Variables and functions for use by the command modules."""

import importlib


class State:
    """Base class for states/commands."""

    def run(self, agent) -> tuple[str, bool]:
        """Run the command to ensure the state."""
        raise NotImplementedError

    def test(self, agent) -> bool:
        """Return True if the state already exists."""
        return False

    def ensure(self, agent) -> tuple[str, bool]:
        """Ensure the state is fulfilled."""
        if not self.test(agent):
            return self.run(agent)
        return "(no changes needed)", False

    def __str__(self):
        return f"<{self.__class__.__qualname__}>"


def require_python_package(module_name, package_name=None):
    """Ensure a Python package is installed."""
    # TODO: Implement this function
    try:
        mod = importlib.import_module(module_name)
    except ImportError:
        raise
    return mod
