"""Base classes and functions."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Optional
import inspect
from collections.abc import Iterable

from pydevops.sh import Shell
from pydevops.utils import get_logger


def sanitize(v: str):
    return v.strip()


def get_class_full_name(cls):
    module = cls.__module__
    if module == "builtins":
        return cls.__qualname__
    return f"{module}.{cls.__qualname__}"


def get_step_full_name(stage: str, step: str):
    stage = sanitize(stage)
    step = sanitize(step)
    return f"/{stage}/{step}"


def apply_aliases(options: dict, aliases: dict):
    result = options.copy()
    for alias, targets in aliases.items():
        result.pop(alias, None)  # Remove alias from the list of options.
        alias_value = options.get(alias, None)
        if alias_value is not None:
            # There is some value in options for that alias.
            if not isinstance(targets, list) and not isinstance(targets, tuple):
                targets = (targets, )
            for target in targets:
                # Put the target option only in the condition where such
                # parameter wasn't specified directly by user
                # (aliases have the lower priority).
                if target not in result:
                    result[target] = alias_value
    return result


@dataclass(frozen=True)
class DevopsCfgContext:
    options: dict

    def has_option(self, key: str):
        return key in self.options

    def get_option(self, key: str):
        return self.options[key]

    def remove_option(self, key: str):
        return self.options.pop(key)


def expand_defaults(defaults, ctx: DevopsCfgContext):
    result = {}
    # Convert all functions to raw values.
    for k, v in defaults.items():
        if callable(v):
            v = v(ctx)
        result[k] = v
    return result


def create_context(env, args, options, cfg):
    options = options.copy()

    defaults = expand_defaults(cfg.defaults, DevopsCfgContext(options))
    options = {**defaults, **options}
    options = apply_aliases(options, cfg.aliases)
    return Context(env=env, args=args, options=options)


@dataclass(frozen=True)
class Environment:
    host: Optional[str]
    docker: Optional[str]
    src_dir: str
    build_dir: str

    @property
    def is_local(self):
        return self.host == "localhost" and self.docker is None


@dataclass(frozen=True)
class SavedContext:
    version: str
    env: Environment = None
    options: dict = field(default_factory=dict)

    @property
    def is_initialized(self):
        return self.env is not None


class Context:
    def __init__(self, env: Environment, args, options: dict):
        self.env = env
        self.args = args
        self.options = options
        self.cmd_exec = Shell()

    def step_view(self, step_name: str):
        """
        Returns a new Context with options limited to a given step.
        """
        step_name = step_name.strip("/")
        stage, step = step_name.split("/")
        stage, step = sanitize(stage), sanitize(step)
        new_options = {}
        for k, v in self.options.items():
            k = k.strip("/")
            parts = k.split("/")
            if len(parts) == 1:
                # Global options. Allow only if it's not the alias name.
                option_name = sanitize(parts[0])
                new_options[option_name] = v
            elif len(parts) == 2:
                option_stage, option_name = parts
                option_stage = sanitize(option_stage)
                option_name = sanitize(option_name)
                if option_stage == stage:
                    new_options[option_name] = v
            elif len(parts) == 3:
                option_stage, option_step, option_name = k.split("/")
                option_stage = sanitize(option_stage)
                option_step = sanitize(option_step)
                option_name = sanitize(option_name)
                if option_stage == stage and option_step == step:
                    new_options[option_name] = v
        return Context(env=self.env, args=self.args, options=new_options)

    def get_param(self, name: str):
        """
        Returns a command-line parameter value,

        :param name: name of the param to return
        """
        try:
            return getattr(self.args, name)
        except AttributeError as e:
            raise KeyError(f"Missing param: {name}")

    def get_option(self, name: str):
        """
        Returns build option value.

        :param name:
        :return:
        """
        try:
            return self.options[name]
        except KeyError as e:
            raise KeyError(f"Missing option: {name}")

    def get_option_default(self, name: str, default: str):
        """
        Returns build option value, or default if the option is not present.
        """
        return self.options.get(name, default)

    def get_options(self) -> Dict[str, str]:
        """
        Returns a copy of options for a given step.

        The returned options are already sanitized, i.e. all trailing
        and leading white spaces are removed.
        """
        return self.options.copy()

    def sh(self, *args, **kwargs):
        return self.cmd_exec.run(*args, **kwargs)

    def rmdir(self, path: str):
        return self.cmd_exec.rmdir(path)

    def mkdir(self, path: str):
        return self.cmd_exec.mkdir(path)

    @property
    def is_local(self):
        return False


class Step(ABC):

    def __init__(self, name):
        self.name = name

    @abstractmethod
    def execute(self, context: Context):
        raise ValueError("Abstract method.")


class Process:
    """
    Base class for the devops process.
    """

    def __init__(self, stages_dictionary, stages, ctx: Context):
        self.stages_dictionary = stages_dictionary
        self.stages = stages
        self.ctx = ctx
        self.logger = get_logger(str(self))

    def execute(self):
        for stage_key in self.stages:
            try:
                self.execute_stage(stage_key)
            except Exception as e:
                self.logger.error(f"Exception while executing "
                                  f"stage: {stage_key}. Check the errors.")
                self.logger.error("Stopping pipeline execution.")
                raise e

    def execute_stage(self, stage: str):
        self.logger.info(f"Executing stage: {stage}")
        steps = self.stages_dictionary[stage]
        # A single class
        if inspect.isclass(steps):
            steps = [(get_class_full_name(steps), steps)]
        elif isinstance(steps, list) or isinstance(steps, tuple):
            # A pair (name, cls)
            if (len(steps) == 2 and isinstance(steps[0], str)
                    and inspect.isclass(steps[1])):
                steps = [steps]
            # A list of [cls1, cls2, cls3]...
            elif all(inspect.isclass(c) for c in steps):
                steps = [(get_class_full_name(c), c) for c in steps]
        names, classes = zip(*steps)
        names = (get_step_full_name(stage, name) for name in names)
        instances = [c(name) for name, c in zip(names, classes)]
        for instance in instances:
            self.logger.info(f"Executing step: {instance.name}")
            try:
                # Create a wrapper for the context, so the step sees only its
                # options.
                step_context = self.ctx.step_view(instance.name)
                self.logger.debug(f"With options: {step_context.options}")
                instance.execute(step_context)
            except Exception as e:
                self.logger.error(f"Exception while executing step: "
                                  f"{instance.name}. Check the errors.")
                raise e

