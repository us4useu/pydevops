from pydevops.base import Step, Context


class Install(Step):

    def execute(self, context: Context):
        src_dir = context.get_param("src_dir")
        build_dir = context.get_param("build_dir")
        build_type = context.get_option("build_type")
        build = context.get_option_default("build", None)
        profile_file = context.get_option_default("profile", None)
        conan_home = context.get_option_default("conan_home", None)
        cmd = f"conan install {src_dir} -if {build_dir} " \
              f"-s build_type={build_type} "
        if build:
            cmd += f"--build={build} "
        if profile_file:
            cmd += f"--profile={profile_file}"
        if conan_home:
            context.sh(cmd, env_extend={"CONAN_USER_HOME": conan_home})
        else:
            context.sh(cmd)
