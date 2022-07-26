import os
from pydevops.base import Step, Context


def _convert_dict_to_kv_params(d: dict):
    result = []
    for k, v in d.items():
        result.append(f"-{k.strip()}={v.strip()}")
    return " ".join(result)


class Configure(Step):
    """
    CMake configure step.
    """

    def execute(self, ctx: Context):
        src_dir = ctx.get_param("src_dir")
        build_dir = ctx.get_param("build_dir")
        options = ctx.get_options()
        generator = options.pop("generator")
        others = _convert_dict_to_kv_params(options)
        ctx.sh(f"cmake -S {src_dir} -B {build_dir} -G {generator} {others}")


class Build(Step):

    def execute(self, ctx: Context):
        src_dir = ctx.get_param("src_dir")
        build_dir = ctx.get_param("build_dir")
        config = ctx.get_option("config")
        n_jobs = ctx.get_option_default("j", 1)
        verbose = ctx.get_option_default("verbose", False)
        cmd = f"cmake --build {build_dir} --config {config} -j {n_jobs}"
        if verbose:
            cmd += " --verbose"
        ctx.sh(cmd)


class Test(Step):
    def execute(self, ctx: Context):
        src_dir = ctx.get_param("src_dir")
        build_dir = ctx.get_param("build_dir")
        config = ctx.get_option("C")
        verbose = ctx.get_option_default("verbose", False)
        # Note: tests have to be run from the build dir
        cwd = os.getcwd()
        try:
            os.chdir(build_dir)
            cmd = f"ctest -C {config}"
            if verbose:
                cmd += " --verbose"
            ctx.sh(cmd)
        finally:
            os.chdir(cwd)


class Install(Step):
    def execute(self, ctx: Context):
        build_dir = ctx.get_param("build_dir")
        config = ctx.get_option("config")
        prefix = ctx.get_option("prefix")
        # Note: tests have to be run from the build dir
        ctx.sh(f"cmake --install {build_dir} "
               f"--prefix {prefix} "
               f"--config {config}")




