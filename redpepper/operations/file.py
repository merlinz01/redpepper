import grp
import hashlib
import io
import json
import logging
import os
import pwd

from redpepper.operations import Operation, Result

logger = logging.getLogger(__name__)


class Installed(Operation):

    def __init__(
        self,
        path,
        source,
        method="hash",
        overwrite=True,
        user=None,
        group=None,
        mode=None,
    ):
        self.path = path
        self.source = source
        self.method = method
        if method not in ["mtime", "hash"]:
            raise ValueError(f"Unknown method: {method}")
        self.overwrite = overwrite
        self.user = user
        if user is not None and not isinstance(user, int):
            self.user = pwd.getpwnam(user).pw_uid
        self.group = group
        if group is not None and not isinstance(group, int):
            self.group = grp.getgrnam(group).gr_gid
        if mode is not None and not isinstance(mode, int):
            mode = int(mode, 8)
        self.mode = mode

    def __str__(self):
        return f'file.Installed("{self.path}" from "{self.source}")'

    def ensure(self, agent):
        result = Result(self)
        # Open in binary writable mode without truncating the file
        try:
            f = open(self.path, "r+b")
        except FileNotFoundError:
            f = open(self.path, "wb")
        with f:
            stat = os.fstat(f.fileno())
            if self.mode is not None and stat.st_mode & 0o777 != self.mode:
                os.fchmod(f.fileno(), self.mode)
                result += (
                    f"Changed mode from 0{stat.st_mode & 0o777:o} to 0{self.mode:o}."
                )
                result.changed = True
            if self.user is not None and stat.st_uid != self.user:
                os.fchown(f.fileno(), self.user, -1)
                result += f"Changed owner from {stat.st_uid} to {self.user}."
                result.changed = True
            if self.group is not None and stat.st_gid != self.group:
                os.fchown(f.fileno(), -1, self.group)
                result += f"Changed group from {stat.st_gid}to {self.group}."
                result.changed = True
            if self.overwrite:
                try:
                    needs_rewritten = self.check_needs_rewritten(agent)
                except ValueError as e:
                    result.exception()
                    return result
                if needs_rewritten:
                    try:
                        nwritten = self.write_file(agent, f)
                    except Exception:
                        result.exception()
                    else:
                        result += f"Wrote {nwritten} bytes to {self.path}."
                        result.changed = True
        return result

    def check_needs_rewritten(self, agent):
        if not self.overwrite:
            return True
        if self.method == "mtime":
            ok, data = agent.request_data("file_mtime", self.source)
            if not ok:
                raise ValueError("Failed to get mtime: %s", data)
            try:
                mtime = float(data)
            except ValueError:
                raise ValueError(f"Invalid mtime received: {data}")
            try:
                existing_mtime = os.path.getmtime(self.path)
            except FileNotFoundError:
                existing_mtime = None
            logger.debug("Mtime of %s: %s vs. %s", self.path, existing_mtime, mtime)
            return existing_mtime == mtime
        elif self.method == "hash":
            ok, hash = agent.request_data("file_hash", self.source)
            if not ok:
                raise ValueError("Failed to get hash: %s", hash)
            existing_hash = self.hash_file(self.path)
            logger.debug("Hash of %s: %s vs. %s", self.path, existing_hash, hash)
            return existing_hash == hash
        return False

    def write_file(self, agent, f: io.BufferedIOBase):
        # Retrieve the entire file into the buffer first so that we don't
        # leave the file in an inconsistent state if the connection is lost
        contents = io.BytesIO()
        while True:
            parameters = {
                "filename": self.source,
                "offset": contents.tell(),
                "length": 64536,
            }
            ok, data = agent.request_data("file_content", json.dumps(parameters))
            if not ok:
                raise ValueError(f"Failed to get file content: {data}")
            if not data:
                break
            contents.write(data)
        f.write(contents.getbuffer())
        f.truncate()
        f.flush()
        os.fsync(f.fileno())
        nwritten = contents.tell()
        contents.close()
        return nwritten

    def hash_file(self, path):
        try:
            hash = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash.update(chunk)
            return hash.digest()
        except (FileNotFoundError, IsADirectoryError):
            return None
