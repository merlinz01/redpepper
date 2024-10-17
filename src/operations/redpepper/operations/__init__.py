import os

from redpepper.common.operations import Operation, Result

__all__ = [
    "Operation",
    "Result",
]

# Set here so it can be changed
custom_operations_dir = os.path.join(os.path.dirname(__file__))
