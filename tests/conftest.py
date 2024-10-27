"""
This module defines globally available fixtures for the test suite.
"""

from tests.agent import agent, agent2
from tests.manager import manager

__all__ = [
    "manager",
    "agent",
    "agent2",
]
