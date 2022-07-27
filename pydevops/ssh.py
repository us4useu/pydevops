import os
import pathlib
from pydevops.sh import Shell


class SshClient:

    def __init__(self, address: str):
        self.host, self.port = self.split_address(address)
        self.cmd_exec = Shell()

    def cp_to_remote(self, src_dir: str, dst_dir: str):
        if src_dir == ".":
            src_dir = os.getcwd()
        port = f"-P{self.port}" if self.port else ""
        options = ""
        if pathlib.Path(src_dir).is_dir():
            options += "-r"
        # TODO Make it OS portable (just use python -c '...')?
        self.sh(f"mkdir -p {dst_dir}")
        # Write the directory to parent.
        dst_dir = str(pathlib.Path(dst_dir).parents[0])
        self.cmd_exec.run(f"scp {options} {port} {src_dir} {self.host}:{dst_dir}")

    def rmdir(self, dir: str):
        # TODO make it OS portable
        self.sh(f"rm -rf {dir}")

    def sh(self, cmd: str):
        port = f"-p{self.port}" if self.port else ""
        self.cmd_exec.run(f"ssh {port} {self.host} {cmd}")

    def split_address(self, address: str):
        parts = address.split(":")
        if len(parts) == 1:
            return address, None
        else:
            return parts[0], parts[1]
