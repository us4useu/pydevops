import os
import shlex
import subprocess
from pydevops.base import *
from pydevops.utils import get_logger


class Sh:
    """
    A current instance of shell prompt (including all the environment
    variables, etc.).

    Currently this is only a localhost implementation.
    """
    def __init__(self, env=None):
        self.logger = get_logger(Sh)
        self.env = env

    def run(self, cmd: str, capture_stdout=False, capture_stderr=False) \
            -> CommandResult:
        self.logger.debug(f"Executing command: {cmd}")
        cmd_tokens = shlex.split(cmd)
        kwargs = {
            "args": cmd_tokens,
            "check": True
        }
        if self.env is not None:
            self.logger.info(f"With environment variables: {self.env}")
            kwargs["env"] = self.env

        stdout = None
        stderr = None
        if capture_stdout:

        # TODO dokonczyc implementacje
        result = subprocess.run(**kwargs)
        return CommandResult(return_code=value, stdout=value, stderr=stderr)

    def source(self, source_path):
        # TODO copy implementation of
        return ShExecutor(env=)


