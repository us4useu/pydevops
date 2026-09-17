from pydevops.base import Step, Context
import os
import shlex

class AddLocalIndex(Step):
    def execute(self, context: Context):
        path_relative = context.get_option("path")
        if path_relative is None:
            raise ValueError("Option 'path' must be provided for conan.AddLocalIndex step.")

        build_dir = context.get_param("build_dir")
        path = os.path.join(build_dir, path_relative)
        path = os.path.normcase(path)
        path = shlex.quote(path)

        cmd = f"conan remote add local-{path_relative} {path} --force"

        context.sh(cmd)

class Install(Step):

    def execute(self, context: Context):
        src_dir = context.get_param("src_dir")
        build_dir = context.get_param("build_dir")
        build_type = context.get_option("build_type")
        build = context.get_option_default("build", None)
        profile_file = context.get_option_default("profile", None)
        conan_home = context.get_option_default("conan_home", None)
        cmd = f"conan install --build=missing {src_dir} --update " \
              f"-s build_type={build_type}"
        #if build:
        #    cmd += f"--build={build} "
        if profile_file:
            cmd += f"--profile={profile_file}"
        if conan_home:
            context.sh(cmd, env_extend={"CONAN_USER_HOME": conan_home})
        else:
            context.sh(cmd)
