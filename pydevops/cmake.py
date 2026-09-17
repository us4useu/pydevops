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
        generator_options = ""
        generator = options.pop("generator", None)
        if generator:
            generator_options = f"-G {generator}"
        toolset = options.pop("toolset", None)
        if toolset:
            generator_options += f" -T {toolset}"
        preset = options.pop("preset", None)
        if preset:
            generator_options += f" --preset {preset}"
        else:
            # This is a very simplified behavior, but it works for us
            generator_options += f"-B {build_dir}"
        others = _convert_dict_to_kv_params(options)
        ctx.sh(f"cmake -S {src_dir} {generator_options} {others}")


class Build(Step):
    def execute(self, ctx: Context):
        src_dir = ctx.get_param("src_dir")
        build_dir = ctx.get_param("build_dir")
        config = ctx.get_option("config")
        n_jobs = ctx.get_option_default("j", 1)
        verbose = ctx.get_option_default("verbose", False)
        preset_or_build_dir = ""
        preset = ctx.get_option_default("preset", None)
        if preset:
            preset_or_build_dir = f" --preset {preset}"
        else:
            preset_or_build_dir = f" {build_dir}"
        cmd = f"cmake --build {preset_or_build_dir} --config {config} -j {n_jobs}"
        if verbose:
            cmd += " --verbose"
        if ctx.has_option("target"):
            target = ctx.get_option("target")
            cmd += f" --target {target}"
        ctx.sh(cmd)


class Test(Step):
    def execute(self, ctx: Context):
        src_dir = ctx.get_param("src_dir")
        build_dir = ctx.get_param("build_dir")
        config = ctx.get_option("C")
        verbose = ctx.get_option_default("verbose", False)
        preset = ctx.get_option_default("preset", None)
        # Note: tests have to be run from the build dir
        cwd = os.getcwd()
        try:
            if not preset:
                os.chdir(build_dir)
            cmd = f"ctest -C {config}"
            if verbose:
                cmd += " --verbose"
            if preset:
                cmd += f" --preset {preset}"
            ctx.sh(cmd)
        finally:
            os.chdir(cwd)


class Install(Step):
    def execute(self, ctx: Context):
        build_dir = ctx.get_param("build_dir")
        config = ctx.get_option("config")
        prefix = ctx.get_option("prefix")
        build_dir_suffix = ctx.get_option_default("build_dir_suffix", "")
        # Note: tests have to be run from the build dir
        ctx.sh(f"cmake --install {build_dir}{build_dir_suffix} "
               f"--prefix {prefix} "
               f"--config {config}")




