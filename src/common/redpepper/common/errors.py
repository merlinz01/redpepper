class RequestError(Exception):
    """Base class for request errors that get reported to the agent."""


class ProtocolError(Exception):
    """Exception raised when a protocol violation is detected"""


class AuthenticationError(Exception):
    """Base class for authentication errors."""
