import os
import pathlib
import shlex
import subprocess
from pydevops.base import *
from pydevops.utils import get_logger
import shutil


@dataclass(frozen=True)
class CommandResult:
    return_code: int
    stdout: str


def rmdir(path: str):
    """
    Removes the given directory. Will throw exception, if the given path
    does not point to a directory. The directory does not have to be empty.

    :param path: path to the directory to remove
    """
    p = pathlib.Path(path)
    if p.is_dir():
        shutil.rmtree(path)
    elif not p.exists():
        # ignore
        pass
    else:
        raise ValueError(f"{path} is not a directory.")


def mkdir(path: str, exist_ok=False):
    """
    Creates new directory.

    :param path: path to directory to create
    """
    os.makedirs(path, exist_ok=exist_ok)


def sanitize_output(stream):
    return stream.decode("UTF-8").strip()


class Shell:
    """
    A current instance of shell prompt (including all the environment
    variables, etc.).

    Currently, this is only a localhost implementation.
    """
    def __init__(self):
        self.logger = get_logger(f"{type(self).__name__}_{id(self)}")

    def run(self, cmd: str, capture_stdout=False, env_extend:dict=None) \
            -> CommandResult:
        self.logger.debug(f"Executing command: {cmd}")
        cmd_tokens = shlex.split(cmd)
        kwargs = {
            "args": cmd_tokens,
            "check": True
        }
        if capture_stdout:
            kwargs["stdout"] = subprocess.PIPE
            kwargs["stderr"] = subprocess.STDOUT

        if env_extend is not None:
            self.logger.debug(f"With additional env variables: {env_extend}")
            parent_env = os.environ
            env = {**parent_env, **env_extend}
            kwargs["env"] = env
        result = subprocess.run(**kwargs)
        stdout = ""
        if capture_stdout:
            stdout = sanitize_output(result.stdout)
        return CommandResult(return_code=result.returncode, stdout=stdout)

    def mkdir(self, path: str, exist_ok=False):
        self.logger.debug(f"Creating directory: {path}")
        return mkdir(path, exist_ok)

    def rmdir(self, path: str):
        self.logger.debug(f"Removing directory: {path}")
        rmdir(path)
