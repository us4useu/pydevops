import argparse
import importlib
import sys
import os.path
from collections import defaultdict
from pydevops.process import Process


def load_cfg(path):
    module_name = "pydevops_cfg"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def parse_options(options_str):
    """
    A list of key=value pairs.
    e.g.
    Values with whitespaces should be in quotation marks.
    """
    result = defaultdict(list)
    for option in options_str:
        key, value = option.split("=")
        key = key.strip()
        value = value.strip()
        result[key].append(value)
    return result


def main():
    parser = argparse.ArgumentParser(description="DevOps Python tools")
    parser.add_argument("--step", dest="step",
                        help="Step to execute, when not provided, "
                             "the sequence of steps will be executed",
                        type=str, required=False, default=None)
    parser.add_argument("--host", dest="host",
                        help="Host on which the command should be executed."
                             " The default `localhost` means that "
                             "the process will be executed on the local "
                             "computer. Otherwise, all communication with "
                             "the remote host will be done via ssh.",
                        type=str, required=False, default="localhost")
    parser.add_argument("--docker", dest="docker",
                        help="Docker image tag (img::image_tag), "
                             "container name/id "
                             "(container::container_name/id) "
                             "or the path to the Dockerfile (file::path). "
                             "By default (None) docker will be not used to "
                             "execute the process.",
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
    args = parser.parse_args()
    step = args.step
    host = args.host
    docker = args.docker
    src_dir = args.src_dir
    build_dir = args.build_dir
    options = parse_options(args.options)
    options["src_dir"] = src_dir
    options["build_dir"] = build_dir
    options["docker"] = docker
    options["host"] = host
    options["step"] = step
    # Remote and/or docker
    if host != "localhost" or docker is not None:
        # TODO reconstruct cmd
        # note: --host should be replaced to localhost
        # note: --docker should be removed
        # create appropriate environment
        # if the directory in the remote
        # 1. start remote process (needed for docker) if necessary
        # 2. checkout
        # 2.

        # specjalne kroki
        # --step=clean jezeli jest ssh process: usun zdalnie zrodla, jezeli jest docker process: usun kontener, w przeciwnym przypadku usun build
        # --step=init: jezeli jest docker: wystartuj kontener dockerowy, w przeciwnym razie nop
        # --step=checkout: jezeli jest remote/docker: zrob git checkout, w przeciwnym przypadku NOP
        # To wszystko powyzsze mogloby byc czescia jednej komendy init?
        # dalej kroki takie jak w przekazanym pliku konfiguracyjnym, tylko wolac zdalnie
        pass
    # Localhost and not Docker
    else:
        cfg = load_cfg(os.path.join(build_dir, "devops.py"))
        steps = cfg.steps
        process = Process(steps, options)
        return process.do()


if __name__ == "__main__":
    sys.exit(main())
