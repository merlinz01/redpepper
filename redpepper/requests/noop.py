from redpepper.manager.manager import AgentConnection
from redpepper.requests import RequestError


def call(conn: AgentConnection, **kwargs):
    raise RequestError("This is a no-op template request module.")
