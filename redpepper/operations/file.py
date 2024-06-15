import base64
import grp
import hashlib
import io
import logging
import os
import pwd

from redpepper.operations import Operation, Result

logger = logging.getLogger(__name__)


class Installed(Operation):
    def __init__(
        self,
        path: str,
        source: str,
        method: str = "hash",
        overwrite: bool = True,
        user: str | int | None = None,
        group: str | int | None = None,
        mode: int | None = None,
    ):
        self.path = path
        self.source = source
        self.method = method
        if method not in ["stat", "hash", "content"]:
            raise ValueError(f"Unknown method: {method}")
        self.overwrite = overwrite
        if user is not None and isinstance(user, str):
            self.user = pwd.getpwnam(user).pw_uid
        else:
            self.user = user
        if group is not None and isinstance(group, str):
            self.group = grp.getgrnam(group).gr_gid
        else:
            self.group = group
        if mode is not None and not isinstance(mode, int):
            mode = int(mode, 8)
        self.mode = mode

    def __str__(self):
        if self.method == "content":
            source = "content"
        else:
            source = f'"{self.source}"'
        return f'file.Installed("{self.path}" from {source})'

    def ensure(self, agent):
        result = Result(self)
        # Open in binary writable mode without truncating the file
        try:
            f = open(self.path, "r+b")
            logger.debug("File %r already exists", self.path)
        except FileNotFoundError:
            f = open(self.path, "wb")
            logger.debug("Creating file %r", self.path)
        mtime = None
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
                result += f"Changed group from {stat.st_gid} to {self.group}."
                result.changed = True
            if self.overwrite:
                try:
                    nwritten, mtime = self.ensure_file_contents(agent, f)
                except Exception:
                    result.exception()
                    return result
                else:
                    if nwritten is not None:
                        result += f"Wrote {nwritten} bytes to {self.path}."
                        result.changed = True
        if mtime is not None:
            os.utime(self.path, (mtime, mtime))
        if not result.changed:
            result += f'File "{self.path}" is already in the specified state.'
        return result

    def ensure_file_contents(self, agent, f: io.BufferedIOBase):
        logger.debug("Comparing file using %s method", self.method)
        rewrite = False
        if self.method == "content":
            try:
                existing = f.read()
            except io.UnsupportedOperation:
                existing = b""
            shouldbe = self.source.encode("utf-8")
            if existing != shouldbe:
                f.seek(0)
                f.write(shouldbe)
                f.truncate()
                f.flush()
                os.fsync(f.fileno())
                nwritten = len(shouldbe)
                return nwritten, None
            return None, None
        remote_stat = agent.request("dataFileStat", path=self.source)
        if self.method == "stat":
            try:
                existing_stat = os.fstat(f.fileno())
                existing_mtime = existing_stat.st_mtime
                existing_size = existing_stat.st_size
            except FileNotFoundError:
                existing_mtime = None
                existing_size = None
            logger.debug(
                "Mtime of %r: %s vs. %s",
                self.path,
                existing_mtime,
                remote_stat["mtime"],
            )
            logger.debug(
                "Size of %r: %s vs. %s", self.path, existing_size, remote_stat["size"]
            )
            rewrite = (
                existing_mtime != remote_stat["mtime"]
                or existing_size != remote_stat["size"]
            )
        elif self.method == "hash":
            hash = agent.request("dataFileHash", path=self.source)
            existing_hash = self.hash_file(f)
            logger.debug("Hash of %s: %s vs. %s", self.path, existing_hash, hash)
            rewrite = existing_hash != hash
        if not rewrite:
            return None, None
        # Retrieve the entire file into the buffer first so that we don't
        # leave the file in an inconsistent state if the connection is lost
        contents = io.BytesIO()
        while True:
            data = agent.request(
                "dataFileContents",
                filename=self.source,
                offset=contents.tell(),
                length=32 * 1024,
            )
            data = base64.b64decode(data)
            if not data:
                break
            contents.write(data)
        f.seek(0)
        f.write(contents.getbuffer())
        f.truncate()
        f.flush()
        os.fsync(f.fileno())
        nwritten = contents.tell()
        contents.close()
        return nwritten, remote_stat["mtime"]

    def hash_file(self, f: io.BufferedIOBase):
        try:
            hash = hashlib.sha256()
            for chunk in iter(lambda: f.read(4096), b""):
                hash.update(chunk)
            return hash.hexdigest()
        except io.UnsupportedOperation:
            return None


class Symlinked(Operation):
    _no_changes_text = "The symlink is already in the specified state."

    def __init__(self, path, target):
        self.path = path
        self.target = target

    def __str__(self):
        return f'file.Symlinked("{self.path}" to "{self.target}")'

    def test(self, agent):
        try:
            existing_target = os.readlink(self.path)
        except FileNotFoundError:
            existing_target = None
        return existing_target == self.target

    def run(self, agent):
        result = Result(self)
        try:
            existing_target = os.readlink(self.path)
        except FileNotFoundError:
            existing_target = None
        if existing_target != self.target:
            try:
                os.symlink(self.target, self.path)
            except FileExistsError:
                os.remove(self.path)
                os.symlink(self.target, self.path)
            result += f"Symlinked {self.path} to {self.target}."
            result.changed = True
        return result


class Dir(Operation):
    def __init__(self, path, user=None, group=None, mode=None):
        self.path = path
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
        return f'file.DirExists("{self.path}")'

    def test(self, agent):
        if not os.path.isdir(self.path):
            return False
        stat = os.stat(self.path)
        if self.mode is not None and stat.st_mode & 0o777 != self.mode:
            return False
        if self.user is not None and stat.st_uid != self.user:
            return False
        if self.group is not None and stat.st_gid != self.group:
            return False
        return True

    def run(self, agent):
        result = Result(self)
        try:
            stat = os.stat(self.path)
        except FileNotFoundError:
            os.mkdir(self.path)
            stat = os.stat(self.path)
            result += f"Created directory {self.path}."
            result.changed = True
        if self.mode is not None and stat.st_mode & 0o777 != self.mode:
            os.chmod(self.path, self.mode)
            result += f"Changed mode from 0{stat.st_mode & 0o777:o} to 0{self.mode:o}."
            result.changed = True
        if self.user is not None and stat.st_uid != self.user:
            os.chown(self.path, self.user, -1)
            result += f"Changed owner from {stat.st_uid} to {self.user}."
            result.changed = True
        if self.group is not None and stat.st_gid != self.group:
            os.chown(self.path, -1, self.group)
            result += f"Changed group from {stat.st_gid} to {self.group}."
            result.changed = True
        return result
