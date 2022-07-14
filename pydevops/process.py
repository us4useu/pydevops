import argparse
import logging
import os.path
from abc import ABC, abstractmethod
import logging
import traceback
from dataclasses import dataclass
import yaml
import pathlib

from pydevops.base import *
from pydevops.utils import get_logger
from pydevops.sh import ShExecutor


class Process:
    """
    Base class for the devops process.
    """

    CFG_FILENAME = "pydevops_cfg.yml"

    def __init__(self, steps, options: dict):
        self.steps = steps
        self.steps_idx = dict([(s.get_id(), s) for s in self.steps])
        self.logger = get_logger(Process)
        self.options = options
        self.step = self.get_step(self.options.get("step_id", None))

    def do(self):
        cmd_exec = ShExecutor()
        build_dir = self.options["build_dir"]
        context = self.get_context(build_dir, cmd_exec, self.options)
        try:
            if self.step is not None:
                self.run_step(self.step, context)
            else:
                for s in self.steps:
                    self.run_step(s, context)
            self.save_context(build_dir, context)
        except Exception as e:
            self.logger.exception(e)
            raise e

    def get_step(self, step_id: str):
        if step_id is None:
            return None
        return self.steps_idx[step_id]

    def run_step(self, step: Step, context: Context):
        if context.is_checkpoint("configured"):
            step.redo(context)
        else:
            step.do(context)

    def get_context(self, path, default_cmd_exec, default_options):
        context_filepath = os.path.join(path, Process.CFG_FILENAME)
        context_file = pathlib.Path(context_filepath)
        checkpoints = set()
        if context_file.exists():
            with open(context_file.absolute(), "r") as f:
                yml_cfg = yaml.safe_load(f)
                checkpoints = set(yml_cfg["checkpoints"])
                default_options = {**default_options, **yml_cfg["options"]}
        return Context(default_cmd_exec, default_options, checkpoints)

    def save_context(self, path, context):
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
        context_filepath = os.path.join(path, Process.CFG_FILENAME)
        with open(context_filepath, "w") as f:
            content = {
                "checkpoints": context.checkpoints,
                "options": context.options
            }
            yaml.dump(content, f)



