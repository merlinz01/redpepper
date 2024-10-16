import hashlib
from typing import BinaryIO

from redpepper.manager.manager import AgentConnection
from redpepper.requests import RequestError


def call(conn: AgentConnection, path: str):
    try:
        fullpath = conn.manager.data_manager.get_data_file_path(conn.agent_id, path)
    except ValueError as e:
        raise RequestError(str(e)) from e
    except FileNotFoundError:
        raise RequestError(f"File not found: {path}")
    try:
        hash = hashlib.sha256()
        with open(fullpath, "rb") as f:
            f: BinaryIO
            for chunk in iter(lambda: f.read(4096), b""):
                hash.update(chunk)
    except FileNotFoundError:
        raise RequestError(f"File not found: {path}")
    return hash.hexdigest()


call.__qualname__ = "request dataFileHash"
