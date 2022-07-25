import argparse
import importlib
import logging
import pathlib
import sys
import os.path
from collections import defaultdict
from typing import Tuple
from pydevops.utils import get_logger
import pickle

from pydevops.base import (
    SavedContext,
    Context,
    Environment,
    Process,
    create_context
)
import pydevops.sh as sh
from pydevops.version import __version__


logger = get_logger("__main__")


CFG_NAME = "devops.py"
CONTEXT_FILE_NAME = "pydevops.cfg"


def load_cfg(path):
    if not pathlib.Path(path).is_file():
        raise ValueError(f"{CFG_NAME} file not found.")
    module_name = "pydevops_cfg"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def read_context(build_dir: str) -> SavedContext:
    ctx_path = os.path.join(build_dir, CONTEXT_FILE_NAME)
    if not pathlib.Path(ctx_path).exists():
        # return context with default values
        return SavedContext(version=__version__)
    else:
        input_path = os.path.join(ctx_path)
        saved_context = pickle.load(open(input_path, "rb"))
        return saved_context


def save_context(build_dir: str, context: SavedContext):
    output_path = os.path.join(build_dir, CONTEXT_FILE_NAME)
    pickle.dump(context, open(output_path, "wb"))


def parse_options(options_str):
    """
    A list of key=value pairs.
    e.g.
    Values with whitespaces should be in quotation marks.
    """
    result = {}
    for option in options_str:
        key, value = option.split("=")
        key = key.strip()
        value = value.strip()
        result[key] = value
    return result


def get_stages_to_execute(args, cfg, saved_context):
    """
    User input arguments have the higher priority than configuration file
    parameters.
    """
    input_stages = args.stage
    init_stages = cfg.init_stages
    default_build_stages = cfg.build_stages
    if len(input_stages) == 0:
        init_stages = [] if saved_context.is_initialized else init_stages
        return init_stages, default_build_stages
    else:
        init_stages_set = set(init_stages)
        init_stages = [s for s in input_stages if s in init_stages_set]
        build_stages = [s for s in input_stages if s not in init_stages_set]
        return init_stages, build_stages


def main():
    parser = argparse.ArgumentParser(description="PyDevOps tools")
    parser.add_argument("--stage", dest="stage",
                        help="Stages to execute, when not provided, "
                             "the sequence of the `init_stages` and "
                             "`build_stages` will be executed",
                        type=str, required=False, default=[],
                        nargs="*")
    parser.add_argument("--host", dest="host",
                        help="Host on which the command should be executed."
                             " The default `localhost` means that "
                             "the process will be executed on the local "
                             "computer. Otherwise, all communication with "
                             "the remote host will be done via ssh. In this"
                             "case, the pattern of the address is: "
                             "user@remote_address:port_number, where"
                             ":port_number is optional. ",
                        type=str, required=False, default="localhost")
    parser.add_argument("--docker", dest="docker",
                        help="Docker image tag (img::image_tag), "
                             "container name/id "
                             "(container::container_name/id) "
                             "or the path to the Dockerfile (file::path). "
                             "By default (None) docker will be not used",
                        type=str, required=False, default=None)
    parser.add_argument("--src_dir", dest="src_dir",
                        help="Path to the source directory.",
                        type=str, required=False, default=".")
    parser.add_argument("--build_dir", dest="build_dir",
                        help="Path to the build directory.",
                        type=str, required=False, default="./build")
    parser.add_argument("--options", dest="options",
                        help="A list of options that should be passed "
                             "to the process steps.",
                        type=str, required=False, default=[],
                        nargs="*")
    parser.add_argument("--clean", dest="clean",
                        help="Start with a fresh build, i.e. delete any "
                             "previously created artifacts. Pipeline will go "
                             "through all init stages.",
                        action="store_true", default=False)
    args = parser.parse_args()
    host = args.host
    docker = args.docker
    src_dir = args.src_dir
    build_dir = args.build_dir
    env_from_params = Environment(host=host, docker=docker, src_dir=src_dir,
                                  build_dir=build_dir)
    cfg = load_cfg(os.path.join(src_dir, CFG_NAME))
    saved_context = read_context(build_dir)

    init_stages, build_stages = get_stages_to_execute(args, cfg, saved_context)
    print(init_stages)
    print(build_stages)

    # Establish current environment.
    options = saved_context.options

    # Read command-line options.
    # Command line options may override the context options.
    options = {**options, **parse_options(args.options)}

    env = saved_context.env
    # Check if the current environment exists and is conformant with the input
    # arguments and pydevops version. If it's not, cleanup and create new
    # environment.
    if (args.clean # Explicit clean
            or saved_context.version != __version__  # A different version of pydevops
            or not saved_context.is_initialized  # Env not yet initialized.
            or not env.__eq__(env_from_params)  # Some change in the env.
    ):
        logger.info(f"Recreating pydevops environment in {build_dir}")
        sh.rmdir(build_dir)
        sh.mkdir(build_dir)
        # create new environment from the input args, set it to saved_context
        env = Environment(host=host, docker=docker, src_dir=src_dir,
                          build_dir=build_dir)
        # Run all init stages, regardless of the input request.
        init_stages = cfg.init_stages
    else:
        logger.info(f"Using pydevops environment stored "
                    f"in {build_dir}/pydevops.cfg")
    saved_context = SavedContext(version=__version__, env=env, options=options)
    save_context(build_dir, saved_context)

    if saved_context.env.is_local:
        # Proceed with execution
        context = create_context(env=saved_context.env, args=args,
                          options=saved_context.options, cfg=cfg)
        if len(init_stages) > 0:
            logger.info(f"Running initialization steps: {init_stages}")
            init_process = Process(cfg.stages, init_stages, ctx=context)
            init_process.execute()

        if len(build_stages) > 0:
            logger.info(f"Running build steps: {build_stages}")
            build_process = Process(cfg.stages, build_stages, ctx=context)
            build_process.execute()
    else:
        # TODO reconstruct cmd
        # note: --host should be replaced to localhost
        # note: --docker should be removed
        # create appropriate environment
        # if the directory in the remote
        # 1. start remote process (needed for docker) if necessary
        # 2. checkout
        # 2.
        # TODO
        pass


if __name__ == "__main__":
    sys.exit(main())
