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


class Shell:
    """
    A current instance of shell prompt (including all the environment
    variables, etc.).

    Currently, this is only a localhost implementation.
    """
    def __init__(self):
        self.logger = get_logger(f"{type(self).__name__}_{id(self)}")

    def run(self, cmd: str) -> CommandResult:
        self.logger.debug(f"Executing command: {cmd}")
        cmd_tokens = shlex.split(cmd)
        kwargs = {
            "args": cmd_tokens,
            "check": True
        }
        result = subprocess.run(**kwargs)
        return CommandResult(return_code=result.returncode)

    def mkdir(self, path: str, exist_ok=False):
        self.logger.debug(f"Creating directory: {path}")
        return mkdir(path, exist_ok)

    def rmdir(self, path: str):
        self.logger.debug(f"Removing directory: {path}")
        rmdir(path)
