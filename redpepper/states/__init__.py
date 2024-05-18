"""Variables and functions for use by the command modules."""

import importlib
import traceback


class State:
    """Base class for states/commands."""

    _name = "<unnamed state>"

    def run(self, agent) -> "StateResult":
        """Run the command to ensure the state."""
        raise NotImplementedError

    def test(self, agent) -> bool:
        """Return True if the state already exists."""
        return False

    def ensure(self, agent) -> "StateResult":
        """Ensure the state is fulfilled."""
        if not self.test(agent):
            return self.run(agent)
        result = StateResult(self._name)
        result += "No changes needed."
        return result

    def __str__(self):
        return f"State {self._name}"


class StateResult:
    """Result of a state run."""

    def __init__(self, name):
        self.name = name
        self.output = ""
        self.changed = False
        self.succeeded = True

    def __str__(self):
        return f"State {self.name} {'succeeded' if self.succeeded else 'failed'}{' (changed)' if self.changed else ''}:\n{self.output}"

    def add_output(self, output):
        """Add output to the result."""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        self.output += output + "\n"

    def __iadd__(self, other):
        """Add output to the result. `result += "some output"`."""
        self.add_output(other)
        return self

    def exception(self):
        """Add exception information to the output."""
        self.add_output(traceback.format_exc())
        self.succeeded = False

    def fail(self, output=None):
        """Mark the result as failed."""
        if output:
            self.add_output(output)
        self.succeeded = False

    def update(self, other: "StateResult"):
        """Update the result with another result."""
        self.add_output(str(other))
        self.changed = self.changed or other.changed
        self.succeeded = self.succeeded and other.succeeded
        return self

    def check_process_result(self, returncode, output, success_retcodes=[0]):
        """Check the result of a process."""
        self.add_output(output)
        if returncode not in success_retcodes:
            self.succeeded = False
            return False
        return True


def require_python_package(module_name, package_name=None):
    """Ensure a Python package is installed."""
    # TODO: Implement this function
    try:
        mod = importlib.import_module(module_name)
    except ImportError:
        raise
    return mod
