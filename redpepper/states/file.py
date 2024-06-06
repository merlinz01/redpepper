import grp
import hashlib
import io
import json
import logging
import os
import pwd

from redpepper.states import State, StateResult

logger = logging.getLogger(__name__)


class Installed(State):
    _name = "file.Installed"

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

    def test(self, agent):
        if not os.path.isfile(self.path):
            logger.debug("File %s does not exist", self.path)
            return False
        stat = os.stat(self.path)
        if self.user is not None and self.user != stat.st_uid:
            return False
        if self.group is not None and self.group != stat.st_gid:
            return False
        if self.mode is not None and self.mode != stat.st_mode:
            return False
        if not self.overwrite:
            return True
        if self.method == "mtime":
            ok, data = agent.request_data("file_mtime", self.source)
            if not ok:
                logger.error("Failed to get mtime: %s", data)
                return False
            try:
                mtime = float(data)
            except ValueError:
                logger.error("Failed to parse mtime: %s", data)
                return False
            return os.path.getmtime(self.path) == mtime
        elif self.method == "hash":
            ok, hash = agent.request_data("file_hash", self.source)
            if not ok:
                logger.error("Failed to get hash: %s", hash)
                return False
            return self.hash_file(self.path) == hash
        return False

    def run(self, agent):
        result = StateResult(self._name)
        if not self.overwrite and os.path.isfile(self.path):
            result += f"File {self.path} already exists, not changing content due to overwrite=False."
            stat = os.stat(self.path)
            if self.mode is not None and stat.st_mode & 0o777 != self.mode:
                os.chmod(self.path, self.mode)
                result += (
                    f"Changed mode from 0{stat.st_mode & 0o777:o} to 0{self.mode:o}."
                )
            if self.user is not None and stat.st_uid != self.user:
                os.chown(self.path, self.user, -1)
                result += f"Changed owner from {stat.st_uid} to {self.user}."
            if self.group is not None and stat.st_gid != self.group:
                os.chown(self.path, -1, self.group)
                result += f"Changed group from {stat.st_gid}to {self.group}."
        contents = io.BytesIO()
        while True:
            parameters = {
                "filename": self.source,
                "offset": contents.tell(),
                "length": 64536,
            }
            ok, data = agent.request_data("file_content", json.dumps(parameters))
            if not ok:
                result.fail("Failed to download file contents: " + data)
                return result
            if not data:
                break
            contents.write(data)
        with open(self.path, "wb") as f:
            stat = os.fstat(f.fileno())
            if self.mode is not None and stat.st_mode & 0o777 != self.mode:
                os.fchmod(f.fileno(), self.mode)
                result += (
                    f"Changed mode from 0{stat.st_mode & 0o777:o} to 0{self.mode:o}."
                )
            if self.user is not None and stat.st_uid != self.user:
                os.fchown(f.fileno(), self.user, -1)
                result += f"Changed owner from {stat.st_uid} to {self.user}."
            if self.group is not None and stat.st_gid != self.group:
                os.fchown(f.fileno(), -1, self.group)
                result += f"Changed group from {stat.st_gid}to {self.group}."
            f.write(contents.getvalue())
        result += f"File {self.path} written with {contents.tell()} bytes."
        contents.close()
        return result

    def hash_file(self, path):
        hash = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash.update(chunk)
        return hash.digest()
