import base64

from redpepper.manager.manager import AgentConnection
from redpepper.requests import RequestError


def call(conn: AgentConnection, filename: str, offset: int, length: int):
    try:
        path = conn.manager.data_manager.get_data_file_path(conn.agent_id, filename)
    except ValueError as e:
        raise RequestError(str(e)) from e
    except FileNotFoundError:
        raise RequestError(f"File not found: {filename}")
    try:
        with open(path, "rb") as f:
            f.seek(offset)
            data = f.read(length)
    except FileNotFoundError as e:
        raise RequestError(f"File not found: {filename}") from e
    return base64.b64encode(data).decode("utf-8")


call.__qualname__ = "request dataFileContents"
