from pydevops.sh import Shell
import os
import pathlib
from pydevops.utils import get_logger


class DockerClient:
    """
    """

    def __init__(self, parameters: str):
        self.logger = get_logger(f"{type(self).__name__}_{id(self)}")
        self.parameters = self._index_parameters(parameters)
        self.image_id = None
        self.cmd_exec = Shell()
        build_params = self.parameters.get("build", None)
        name = self.parameters["name"]
        if build_params is not None:
            self.cmd_exec.run(f"docker build . {build_params} -t {name}")
            # Do not build the image on the next run.
            self.parameters.pop("build")
        # Use the latest image with a given name
        self.image_id = self.cmd_exec.run(f"docker images -q {name}",
                                          capture_stdout=True).stdout

    def cp_to_remote(self, src_dir: str, dst_dir: str):
        if src_dir == ".":
            src_dir = os.getcwd()
        options = ""
        if pathlib.Path(src_dir).is_dir():
            options += "-r"
        # Write the directory to parent.
        dst_dir_parent = str(pathlib.Path(dst_dir).parents[0])
        self.mkdir(dst_dir_parent)
        self.sh(f"cp -r {src_dir} {dst_dir}")

    def rmdir(self, dir: str):
        self.sh(f"rm -rf {dir}")

    def mkdir(self, dir: str):
        self.sh(f"mkdir -p {dir}")

    def rename(self, src: str, dst: str):
        self.sh(f"mv {src} {dst}")

    def sh(self, cmd: str):
        if self.image_id is None:
            raise ValueError("Build docker image first.")
        run_params = self.parameters.get("run", "")
        self.cmd_exec.run(f"docker run --rm {run_params} {self.image_id} -l -c \"{cmd}\"")

    @property
    def params(self):
        result = []
        for k, v in self.parameters.items():
            result.append(f"{k}::{v}")
        return ";".join(result)

    def _index_parameters(self, params: str) -> dict:
        params = params.strip().strip(";")
        params = params.split(";")
        result = {}
        for p in params:
            p = p.strip().strip("::")
            p = p.split("::")
            if len(p) != 2:
                raise ValueError("Syntax error in docker options; each options"
                                 "should have a format name::params")
            key, values = p
            result[key] = values
        return result
