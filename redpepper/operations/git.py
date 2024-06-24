import os
import pwd
import subprocess

from redpepper.operations import Operation, Result


class UpToDate(Operation):
    def __init__(
        self,
        target,
        repo,
        force_pull=False,
        rebase=None,
        ff_only=False,
        user=None,
        identity=None,
        depth=None,
        recurse_submodules=False,
    ):
        self.target = target
        self.repo = repo
        self.force_pull = force_pull
        self.rebase = rebase
        self.ff_only = ff_only
        self.user = user
        self.identity = identity
        self.depth = depth
        self.recurse_submodules = recurse_submodules

    def __str__(self):
        return f'git.UpToDate({self.target} from "{self.repo}")'

    def ensure(self, agent):
        result = Result(self)
        clone = False
        if not os.path.isdir(self.target):
            clone = True
        elif not os.path.isdir(os.path.join(self.target, ".git")):
            # git allows empty directories
            clone = True

        git_cmd = ["git"]
        if clone:
            git_cmd.append("clone")
            git_cmd.append(self.repo)
            git_cmd.append(self.target)
        else:
            git_cmd.append("-C")
            git_cmd.append(self.target)
            git_cmd.append("pull")
            if self.force_pull:
                git_cmd.append("--force")
            if self.rebase is not None:
                if self.rebase:
                    git_cmd.append("--rebase")
                else:
                    git_cmd.append("--no-rebase")
            if self.ff_only:
                git_cmd.append("--ff-only")
        if self.depth:
            git_cmd.append("--depth")
            git_cmd.append(str(self.depth))
        if self.recurse_submodules:
            git_cmd.append("--recurse-submodules")

        kw = {}
        kw["env"] = os.environ.copy()
        if self.user:
            kw["user"] = self.user
            kw["env"]["HOME"] = pwd.getpwnam(self.user).pw_dir
        if self.identity:
            kw["env"]["GIT_SSH_COMMAND"] = f'ssh -i "{self.identity}"'

        p = subprocess.run(
            git_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kw
        )
        if not result.check_completed_process(p).succeeded:
            return result

        if clone:
            result.changed = True
        elif "Already up to date" not in p.stdout:
            result.changed = True

        return result
