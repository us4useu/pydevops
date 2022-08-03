import os
import pathlib
from pydevops.sh import Shell


class SshClient:

    def __init__(self, address: str, start_dir: str):
        """


        :param start_dir: execute commands with this current working directory 
        """

        self.host, self.port = self.split_address(address)
        self.cmd_exec = Shell()
        self.start_dir = start_dir

    def cp_to_remote(self, src_dir: str, dst_dir: str):
        if src_dir == ".":
            src_dir = os.getcwd()
        port = f"-P{self.port}" if self.port else ""
        options = ""
        if pathlib.Path(src_dir).is_dir():
            options += "-r"
        # Write the directory to parent.
        dst_dir_parent = str(pathlib.Path(dst_dir).parents[0])
        dst_dir_name = str(pathlib.Path(dst_dir).name)
        src_dir_name = str(pathlib.Path(src_dir).name)
        self.mkdir(dst_dir_parent)
        self.cmd_exec.run(f"scp {options} {port} {src_dir} {self.host}:{dst_dir_parent}")
        if dst_dir_name != src_dir_name:
            # TODO note below will not work correctly if in the dst dir there is
            # already some directory named as the src dirrectory.
            self.rename(os.path.join(dst_dir_parent, src_dir_name), dst_dir)

    def rmdir(self, dir: str):
        # The below works in Windows cmd and unix bash.
        self.sh(f"rm -rf {dir}")
        # self.sh(f"'python -c \"import shutil;shutil.rmtree(\\\"{dir}\\\", ignore_errors=True)\"'")

    def mkdir(self, dir: str):
        self.sh(f"'python -c \"import pathlib; pathlib.Path(\\\"{dir}\\\").mkdir(parents=True, exist_ok=True)\"'")

    def rename(self, src: str, dst: str):
        self.sh(f"'python -c \"import os;os.rename(\\\"{src}\\\", \\\"{dst}\\\")\"'")

    def sh(self, cmd: str):
        port = f"-p{self.port}" if self.port else ""
        self.cmd_exec.run(f"ssh {port} {self.host} cd {self.start_dir}; {cmd}")

    def split_address(self, address: str):
        parts = address.split(":")
        if len(parts) == 1:
            return address, None
        else:
            return parts[0], parts[1]
