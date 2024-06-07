"""Variables and functions for use by the operation modules."""

import importlib
import subprocess
import traceback
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import redpepper.agent.agent


class Operation:
    """Base class for operations."""

    _no_changes_text = "No changes needed."

    def run(self, agent: "redpepper.agent.agent.Agent") -> "Result":
        """Run the operation to ensure the condition exists. Assume test() returned False."""
        raise NotImplementedError

    def test(self, agent: "redpepper.agent.agent.Agent") -> bool:
        """Return True if the condition created by this operation already exists."""
        return False

    def ensure(self, agent: "redpepper.agent.agent.Agent") -> "Result":
        """Ensure that the condition created by this operation exists, running the operation if the test returns False."""
        if not self.test(agent):
            return self.run(agent)
        result = Result(self)
        result += self._no_changes_text
        return result

    def __str__(self):
        return type(self).__name__


class Result:
    """Result of a state run."""

    def __init__(self, name):
        self.name = name
        self.output = ""
        self.changed = False
        self.succeeded = True

    def __str__(self):
        return f"Operation {self.name}{' succeeded' if self.succeeded else ' failed'}{' (changed)' if self.changed else ''}:\n{self.output.rstrip()}"

    def __repr__(self):
        return f"<Result {self.name}{' succeeded' if self.succeeded else ' failed'}{' (changed)' if self.changed else ''}>"

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

    def update(self, other: "Result", raw_output=False):
        """Update the result with another result."""
        if raw_output:
            self.add_output(other.output)
        else:
            self.add_output(str(other))
        self.changed = self.changed or other.changed
        self.succeeded = self.succeeded and other.succeeded
        return self

    def check_completed_process(self, process, success_retcodes=[0]):
        """Check the result of a subprocess.CompletedProcess."""
        if process.stdout:
            self.add_output(process.stdout.rstrip())
        if process.stderr:
            self.add_output("Stderr:\n" + process.stderr.rstrip())
        if process.returncode not in success_retcodes:
            self.add_output(f"Command failed with return code {process.returncode}")
            self.succeeded = False
        return self


def require_python_package(module_name, pip_package=None):
    """Ensure a Python package is installed, and import it."""
    try:
        mod = importlib.import_module(module_name)
    except ImportError:
        try:
            subprocess.check_call(["pip", "install", pip_package or module_name])
        except subprocess.CalledProcessError:
            raise ImportError(f"Failed to install {pip_package or module_name}")
        else:
            try:
                mod = importlib.import_module(module_name)
            except ImportError:
                raise ImportError(
                    f"Failed to import {module_name} after attempting to install it"
                )
    return mod
