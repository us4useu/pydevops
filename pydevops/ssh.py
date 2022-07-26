from pydevops.sh import Shell


class SshClient:

    def __init__(self, address: str):
        self.host, self.port = self.split_address(address)
        self.cmd_exec = Shell()

    def cp_to_remote(self, src_dir: str, dst_dir: str):
        port = f"-P{self.port}" if self.port else ""
        self.cmd_exec.run(f"scp {port} {src_dir} {self.host}:{dst_dir}")

    def sh(self, cmd: str):
        port = f"-p{self.port}" if self.port else ""
        self.cmd_exec.run(f"ssh {port} {self.host} {cmd}")

    def split_address(self, address: str):
        parts = address.split(":")
        if len(parts) == 1:
            return address, None
        else:
            return parts[0], parts[1]
