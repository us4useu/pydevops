import argparse
import dataclasses
import importlib
import importlib.util
import logging
import pathlib
import sys
import os.path
from collections import defaultdict
from collections.abc import Iterable
from typing import Tuple
import pickle

from pydevops.utils import get_logger
from pydevops.base import (
    SavedContext,
    Context,
    Environment,
    Process,
    create_context
)
import pydevops.sh as sh
from pydevops.version import __version__
from pydevops.docker import DockerClient
from pydevops.ssh import SshClient

logger = get_logger("__main__")

CFG_NAME = "devops.py"
CONTEXT_FILE_NAME = "pydevops.cfg"


def load_cfg(path):
    if not pathlib.Path(path).is_file():
        raise ValueError(f"{path} file not found.")
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


def save_context(build_dir: str, context: SavedContext, secrets):
    if secrets is not None:
        # Remove options from the secrets list, before saving the context.
        options = context.options
        for secret in secrets:
            result = options.pop(secret, None)
            if result is None:
                raise ValueError(f"There is option with key: {secret}")
        context = dataclasses.replace(context, options=options)
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


def to_args_string(args_dict: dict, double_escape_str: bool = False):
    result = []
    for k, v in args_dict.items():
        if v is None:
            # Ignore None values
            continue
        if isinstance(v, Iterable) and not isinstance(v, str):
            if len(v) == 0:
                continue
            v = " ".join(v)
        if isinstance(v, str) and k != "options":
            # Make sure the parameters will be properly enclosed by quotes"
            # In the case of ssh communication, a double quotes may be 
            # necessary (so the remote command also gets quoted parameters).
            if double_escape_str:
                v = fr'"\"{v}\""'
            else:
                v = fr'"{v}"'
        elif isinstance(v, bool):
            if v:
                # Put an empty flag
                v = ""
            else:
                # Skip this parameter: we use only flags here
                continue
        result.append(f"--{k} {v}")
    return " ".join(result)


def sanitize_remote_options(options):
    kvs = (v.strip().split("=") for v in options)
    kvs = [f'{k}=\\"{v}\\"' for k, v in kvs]
    return " ".join(kvs)


def cleanup(src_dir, build_dir, args):
    docker = args.docker
    logger.info(f"Recreating pydevops environment in {build_dir}")
    sh.rmdir(build_dir)
    sh.mkdir(build_dir)
    # create new environment from the input args, set it to saved_context
    env = Environment(host=args.host, docker=docker, src_dir=src_dir,
                      build_dir=build_dir)
    return env


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
                        help="Docker image tag (img:image_tag), "
                             "container name/id "
                             "(container:container_name/id) "
                             "or the path to the Dockerfile (file:path). "
                             "By default (None) docker will be not used",
                        type=str, required=False, default=None)
    parser.add_argument("--ssh_src_dir", dest="ssh_src_dir",
                        help="Path to the remote host source directory.",
                        type=str, required=False, default=None)
    parser.add_argument("--ssh_build_dir", dest="ssh_build_dir",
                        help="Path to the remote host build directory."
                             "This directory will be used to keep the "
                             "pydevops.cfg file for the local machine.",
                        type=str, required=False, default=None)
    parser.add_argument("--docker_src_dir", dest="docker_src_dir",
                        help="Path to the docker container's source directory.",
                        type=str, required=False, default=None)
    parser.add_argument("--docker_build_dir", dest="docker_build_dir",
                        help="Path to the docker container's build directory.",
                        type=str, required=False, default=None)
    parser.add_argument("--src_dir", dest="src_dir",
                        help="Path to the host source directory.",
                        type=str, required=False, default=".")
    parser.add_argument("--build_dir", dest="build_dir",
                        help="Path to the host build directory.",
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
    parser.add_argument("--secrets", dest="secrets",
                        help="A list of option names that should be not saved "
                             "to the context file. Use it e.g. to avoid "
                             "saving sensitive data like personal "
                             "authentication tokens.",
                        type=str, required=False, default=None,
                        nargs="*")
    logger.debug(f"SYS ARGV: {sys.argv}")
    args = parser.parse_args()
    logger.debug(f"OPTIONS: {args.options}")
    host = args.host
    docker = args.docker
    src_dir = args.src_dir
    build_dir = args.build_dir
    env_from_params = Environment(host=host, docker=docker, src_dir=src_dir,
                                  build_dir=build_dir)
    cfg = load_cfg(os.path.join(src_dir, CFG_NAME))
    env = None
    ctx_file_exists = (pathlib.Path(build_dir) / pathlib.Path(
        CONTEXT_FILE_NAME)).exists()
    if args.clean or not ctx_file_exists:
        env = cleanup(src_dir, build_dir, args)

    saved_context = read_context(build_dir)
    init_stages, build_stages = get_stages_to_execute(args, cfg, saved_context)
    if not saved_context.is_initialized:
        saved_context = dataclasses.replace(saved_context, env=env)

    # Establish current environment.
    options = saved_context.options
    # Read command-line options.
    # Command line options may override the context options.
    options = {**options, **parse_options(args.options)}

    env = saved_context.env
    saved_context = SavedContext(version=__version__, env=env, options=options)

    if saved_context.env.is_local:
        # Proceed with execution
        context = create_context(env=saved_context.env, args=args,
                                 options=saved_context.options, cfg=cfg)
        if len(init_stages) > 0:
            logger.info(f"Running initialization steps: {init_stages}")
            init_process = Process(cfg.stages, init_stages, ctx=context)
            init_process.execute()

        save_context(build_dir, saved_context, args.secrets)

        if len(build_stages) > 0:
            logger.info(f"Running build steps: {build_stages}")
            build_process = Process(cfg.stages, build_stages, ctx=context)
            build_process.execute()
    else:
        # Now we are running pydevops on a local machine and executing pipeline
        # on remote machine.
        # Init connection with the remote machine and translate all the options
        # to appropriate settings for remote machine.
        client = None
        remote_args = vars(args)
        host_src_dir = remote_args.pop("src_dir")
        host_build_dir = remote_args.pop("build_dir")
        if "options" in remote_args:
            # Convert each option value to string, to avoid passing
            # e.g. description=Build #4 test instead of 
            # description="Build #4 test"
            remote_args["options"] = sanitize_remote_options(
                remote_args["options"])

        if saved_context.env.host != "localhost":
            # Remote host.
            # Move the execution to the remote host.
            ssh_src_dir = remote_args.pop("ssh_src_dir")
            ssh_build_dir = remote_args.pop("ssh_build_dir")

            remote_args["src_dir"] = ssh_src_dir
            remote_args["build_dir"] = ssh_build_dir
            remote_args["host"] = "localhost"
            remote_args = to_args_string(remote_args, double_escape_str=True)
            client = SshClient(address=saved_context.env.host,
                               start_dir=args.src_dir)
            if args.clean:
                client.rmdir(ssh_src_dir, cd_to_start_dir=False)
                client.rmdir(ssh_build_dir, cd_to_start_dir=False)
                client.cp_to_remote(src_dir, ssh_src_dir, cd_to_start_dir=False)
            client.sh(f"pydevops {remote_args}")
            save_context(build_dir, saved_context, args.secrets)
        elif saved_context.env.docker is not None:
            docker_src_dir = remote_args.pop("docker_src_dir")
            docker_build_dir = remote_args.pop("docker_build_dir")

            remote_args["src_dir"] = docker_src_dir
            remote_args["build_dir"] = docker_build_dir
            # Remove docker attribute (now we will execute commands in the
            # docker container).
            remote_args.pop("docker")
            remote_args = to_args_string(remote_args)
            client = DockerClient(parameters=saved_context.env.docker)
            # Update local SavedContext:
            # in the next try not to build new image, but simply run the
            # existing.
            env = dataclasses.replace(env, docker=client.params)
            saved_context = SavedContext(version=__version__, env=env,
                                         options=options)
            if args.clean:
                logger.info("Cleaning up docker target directories...")
                client.rmdir(docker_src_dir)
                client.rmdir(docker_build_dir)
                client.cp_to_remote(src_dir, docker_src_dir)
            else:
                logger.info("No clean.")
            client.sh(f"pydevops {remote_args}")
            save_context(build_dir, saved_context, args.secrets)


if __name__ == "__main__":
    sys.exit(main())
