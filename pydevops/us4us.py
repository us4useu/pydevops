import os

from pydevops.base import Step, Context
from pydevops.sh import Shell


class PublishDocs(Step):
    """
    Publishes docs in a given repository.
    :param install_dir: path to the directory with release artifacts. Assumes
      that the documentation is located in the docs/html subdirectory.
    """

    def __init__(self, name):
        super().__init__(name)

    def execute(self, context: Context):
        install_dir = ctx.get_option("install_dir")
        repository = ctx.get_option("repository")
        commit_msg = ctx.get_option_default("commit_msg", "")
        version = ctx.get_param("version")
        self.publish(context, repository, release_dir, commit_title, version)

    def git_commit(self, commit_msg: str):
        params = ["git", "commit", "-m", "'"+msg+"'"]
        print("Calling: %s"%(" ".join(params)))
        try:
            out = subprocess.check_output(params)
        except subprocess.CalledProcessError as e:
            out = str(e.output)
            if "nothing to commit" in out:
                return "ntc"
            else:
                return "fail"
        print("Commit output: %s" % out)
        return "ok"

    def publish(self, ctx, repository, install_dir, commit_msg, version):
        cwd = os.getcwd()
        _, repository_name = os.path.split(repository)
        repository_name, _ = repository_name.split(".")
        try:
            ctx.rmdir(repository_name)
            ctx.sh(f"git clone {repository}")
            version = version.strip()
            version_dir = os.path.join(repository_name, "releases", version)
            docs_dir = os.path.join(install_dir, "docs", "html")
            ctx.rmdir(version_dir)
            ctx.mkdir(version_dir)
            language_doc_dirs = os.listdir(docs_dir)
            # Copy documentation for each language.
            for d in language_doc_dirs:
                dst = os.path.join(docs_dir, d)
                src = os.path.join(release_dir, d)
                shutil.copytree(dst, src)
            os.chdir(repository_name)
            ctx.sh("git add -A")
            commit_msg = f"Updated docs: {commit_msg} (host: {platform.node()})"
            result = git_commit(commit_msg)
            if result == 'ntc':
                print("Nothing to commit")
                return
            elif result != "ok":
                raise ValueError("Something wrong when commiting the changes,"
                                 "check the errors in log.")
            ctx.sh(f"git push {repository}")
        finally:
            os.chdir(cwd)
            shutil.rmtree(repository_name, ignore_errors=True)


class PublishReleases:
    pass