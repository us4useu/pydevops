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

    def cp_to_remote(self, src_dir: str, dst_dir: str, cd_to_start_dir=True):
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
        self.mkdir(dst_dir_parent, cd_to_start_dir=cd_to_start_dir)
        self.cmd_exec.run(f"scp {options} {port} {src_dir} {self.host}:{dst_dir_parent}")
        if dst_dir_name != src_dir_name:
            # TODO note below will not work correctly if in the dst dir there is
            # already some directory named as the src dirrectory.
            self.rename(os.path.join(dst_dir_parent, src_dir_name), dst_dir,
                        cd_to_start_dir=cd_to_start_dir)

    def rmdir(self, dir: str, cd_to_start_dir=True):
        # The below works in Windows cmd and unix bash.
        self.sh(f"rm -rf {dir}", cd_to_start_dir=cd_to_start_dir)

    def mkdir(self, dir: str, cd_to_start_dir=True):
        self.sh(f"'python -c \"import pathlib; pathlib.Path(\\\"{dir}\\\").mkdir(parents=True, exist_ok=True)\"'",
                cd_to_start_dir=cd_to_start_dir)

    def rename(self, src: str, dst: str, cd_to_start_dir=True):
        self.sh(f"'python -c \"import os;os.rename(\\\"{src}\\\", \\\"{dst}\\\")\"'",
                cd_to_start_dir=cd_to_start_dir)

    def sh(self, cmd: str, cd_to_start_dir=True):
        port = f"-p{self.port}" if self.port else ""
        start_cd_cmd = f"cd {self.start_dir} && " if cd_to_start_dir else ""
        self.cmd_exec.run(f"ssh {port} {self.host} {start_cd_cmd} {cmd}")

    def split_address(self, address: str):
        parts = address.split(":")
        if len(parts) == 1:
            return address, None
        else:
            return parts[0], parts[1]
