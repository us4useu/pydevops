"""Base classes and functions."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


class Step(ABC):

    @abstractmethod
    def do(self, context):
        raise ValueError("Abstract method.")

    def redo(self, context):
        return self.do(context)

    @abstractmethod
    def get_id(self):
        raise ValueError("Abstract method")


class StepContext:
    pass

class Environment(ABC):

    @abstractmethod
    def get_cmd(self, cmd: str):
        raise ValueError("Abstract method.")

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


@dataclass(frozen=True)
class CommandResult:
    return_code: int
    stdout: str
    stderr: str


class Shell(Environment):

    @abstractmethod
    def run(self, cmd: str) -> CommandResult:
        raise ValueError("Abstract method.")


class CompositeCommandExecutor(Shell):

    def __init__(self, environments):
        self.environments = environments
        self.interface_environment = self.environments[0]
        self.backend_environment = self.environments[-1]

    def get_cmd(self, cmd: str) -> str:
        for e in self.environments:
            cmd = e.get_cmd(cmd)
        return cmd

    def run(self, cmd: str):
        cmd = self.get_cmd(cmd)
        return self.interface_environment.run(cmd)

    def read_context(self, path):
        # TODO read context from the most inner environment
        return self.environments[-1].get_context()

    def save_context(self, path, context):
        self.environments[-1].save_context
        pass


class Context:

    def __init__(self, command_executor: Shell, options: dict,
                 checkpoints: set):
        self.command_executor = command_executor
        self.options = options
        self.checkpoints = checkpoints

    def run(self, cmd: str):
        self.command_executor.run(cmd)

    def get_option(self, key: str, default=None):
        return self.options.get(key, default)

    def set_checkpoint(self, checkpoint):
        self.checkpoints.add(checkpoint)

    def is_checkpoint(self, checkpoint):
        return checkpoint in self.checkpoints


