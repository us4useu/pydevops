from pydevops.base import Step, Context


class Install(Step):

    def execute(self, context: Context):
        src_dir = context.get_param("src_dir")
        build_dir = context.get_param("build_dir")
        build_type = context.get_option("build_type")
        build = context.get_option_default("build", None)
        cmd = f"conan install {src_dir} -if {build_dir} " \
              f"-s build_type={build_type}"
        if build:
            cmd += f"--build={build}"
        context.sh(cmd)
