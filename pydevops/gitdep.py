from pydevops.base import Step, Context
import os
import platform
import shutil
import shlex

class Fetch(Step):

    def execute(self, context: Context):
        repo = context.get_option("repo")
        if repo is None:
            raise ValueError("Option 'repo' must be provided for gitdeps."
                             "Fetch step.")

        revision = context.get_option("revision")
        if revision is None:
            raise ValueError("Option 'revision' must be provided for gitdeps."
                             "Fetch step.")
        path_relative = context.get_option("path")
        if path_relative is None:
            raise ValueError("Option 'path' must be provided for gitdeps."
                             "Fetch step.")

        remove_old = context.get_option_default("remove_old", True)

        build_dir = context.get_param("build_dir")

        path = os.path.join(build_dir, path_relative)
        path = os.path.normcase(path)
        path = shlex.quote(path)

        if remove_old and os.path.exists(path):
            # special handling for Windows: use force.
            if platform.system() == "Windows":
                cmd = f'rd /s /q "{path}"'
                context.sh(cmd)
            else:
                shutil.rmtree(path)

        cmd = f"git clone --depth 1 --branch {revision} {repo} {path}"
        context.sh(cmd)