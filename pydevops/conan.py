from pydevops.base import Step, Context
from pydevops.utils import is_version_at_least
import os
import re


class Install(Step):

    def execute(self, context: Context):
        src_dir = context.get_param("src_dir")
        build_dir = context.get_param("build_dir")
        build_type = context.get_option("build_type")
        build = context.get_option_default("build", None)
        profile_file = context.get_option_default("profile", None)
        conan_home = context.get_option_default("conan_home", None)

        conan_version = context.sh("conan --version", capture_stdout=True).stdout
        m = re.search(r"\d+\.\d+(?:\.\d+)?", conan_version)
        if not m:
            raise RuntimeError(f"Could not parse Conan version from: {conan_version!r}")

        if is_version_at_least("2.0", m.group(0)):
            install_folder_flag = f"--output-folder={build_dir}"
            home_env = {"CONAN_HOME": conan_home} if conan_home else None
        else:
            install_folder_flag = f"--install-folder={build_dir}"
            home_env = {"CONAN_USER_HOME": conan_home} if conan_home else None

        cmd = (
            f"conan install {src_dir} --build=missing --update "
            f"-s build_type={build_type} "
            f"{install_folder_flag}"
        )

        if build:
            cmd += f" --build={build}"
        if profile_file:
            cmd += f" --profile={profile_file}"

        if home_env:
            context.sh(cmd, env_extend=home_env)
        else:
            context.sh(cmd)
