import os

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
        stat = os.stat(fullpath)
        mtime = stat.st_mtime
        size = stat.st_size
    except FileNotFoundError:
        raise RequestError(f"File not found: {path}")
    return {
        "mtime": mtime,
        "size": size,
    }


call.__qualname__ = "request dataFileStat"
