import os
import pathlib
import platform
import shutil

import requests
import date
import platform
import tempfile
import glob

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


class PublishReleases(Step):
    """
    Publishes given artifacts located on the current host in the given
    repository as a given dst_artifact.

    If the src artifact is a regular file, it will be renamed to the
    given dst_artifact (if provided).

    If the src artifact is a directory, it will packed into a zip file,
    and renamed to the given dst_artifact name (if provided).

    src_artifact parameter can contain wildcards, so it's possible to publish
    multiple assets in a single run (or to publish an asset, whose full name we
    do not know).

    If there is no release with the given release_name, it will be created.

    Release name with pattern different than "^v[0-9]+\.[0-9]+\.[0-9]+$"
    will be marked as pre-release.

    If the release is pre-release, a new tag with the same name as branch
    will be created.

    Note: if there are multiple artifacts pointed by src_artifact, and all
    of them are regular files, the name of the artifacts will not be changed
    to the dst_artifact. If there are multiple files and some of them are
    directories, all the files will be zipped to a single dst_artifact.zip file.

    :param release_name: target release name
    :param dst_artifact: the name of the artifact (asset) to create, optional,
      if not provided, the src_artifact name will be used
    :param src_artifact: the path to the source artifact(s) (assets), multiple
      patterns can be specified using semicolor, e.g. pattern1;pattern2
    :param token: Github Personal Access Token (PAT)
    :param description: description of the release.
    :param repository: repository name, e.g. us4useu/arrus
    :param append_stage_description: if set to true, the provided description
      will be extended with signature "stage_name: date, host"
    :param is_zip: whether all the artifacts should be zipped to a single zip
      (with the dst_artifact name), all whether each artifact should be
      uploaded separately.
    """
    def __init__(self, name):
        super().__init__(name)

    def execute(self, context: Context):
        release_name = ctx.get_option("release_name")
        src_artifact = ctx.get_option("src_artifact")
        dst_artifact = ctx.get_option("dst_artifact")
        repository_name = ctx.get_option("repository_name")
        token = ctx.get_option("token")
        description = ctx.get_option_default("description", "")
        append_stage_description = ctx.get_option_default("append_stage_description", False)

        if append_stage_description:
            current_date = date.today().strftime("%d-%m-%Y")
            hostname = platform.node()
            suffix = f"stage {self.get_stage_name()}: {current_date} {hostname}"
            if len(description) > 0:
                suffix = f" {suffix}"
            description = f"{description}{suffix}"

        is_prerelease = not bool(re.match("^v[0-9]+\.[0-9]+\.[0-9]+$", release_name))

        release_id = self.create_release(
            repository_name=repository_name,
            release=release_name,
            body=description,
            prerelease=is_prerelease,
            token=token)
        with tempfile.TemporaryDirectory() as tempdirname:
            artifacts = self.prepare_artifacts(
                src_artifact=src_artifact,
                dst_artifact=dst_artifact,
                workdir=tempdirname,
            )
            for artifact in artifacts:
                self.publish_asset(
                    repository_name=repository_name,
                    asset_path=artifact,
                    token=token)

    def create_release(self, repository_name, release, body, token, prerelease):
        """
        Create new release, using the given parameters.
        If the release already exists, update it (append to the description
        of the release the body provided as an input).
        """
        release_tag = release if not prerelease else f"{release}-first"
        target_commitish = "master" if not prerelease else release
        print(f"Creating release: "
              f"repository_name: {repository_name}, "
              f"release (tag_name): {release} "
              f"body: {body}")
        response = requests.post(url=self.get_api_url(repository_name),
                headers={
                    "Authorization": f"token {token}"
                },
                json={
                    "tag_name": release_tag,
                    "target_commitish": target_commitish,
                    "name": release,
                    "body": body,
                    "draft": False,
                    "prerelease": prerelease
                }
        )
        # Check if the release already exists. If it is, just update it.
        if not response.ok:
            resp = response.json()
            if "errors" not in resp:
                print(resp)
                response.raise_for_status()
            elif resp["errors"][0]["code"] == "already_exists":
                print(f"RELEASE for tag {release_tag} EXISTS, UPDATING IT")
                r = self.get_release_by_tag(
                    repository_name=repository_name,
                    release_tag=release_tag,
                    token=token
                )
                r.raise_for_status()
                release_id = r.json()["id"]
                current_body = r.json()["body"]
                # Append description after new line.
                new_body = f"{current_body}\n{body}"
                r = self.edit_release(
                    repository_name=repository_name,
                    release_id=release_id,
                    release_tag=release_tag,
                    body=new_body,
                    target_commitish=target_commitish,
                    prerelease=prerelease,
                    token=token)
                r.raise_for_status()
                return release_id
            else:
                print(resp)
                response.raise_for_status()
        else:
            release_id = response.json()["id"]
            return release_id

    def get_release_by_tag(self, repository_name, release_tag, token):
        print("Getting release by tag")
        return requests.get(
            url=f"{get_api_url(repository_name)}/tags/{release_tag}",
            headers={
                "Authorization": f"token {token}"
            }
        )

    def edit_release(self, repository_name, release_id, release_tag, body,
                     target_commitish, prerelease, token):
        print("Editing release")
        return requests.patch(
            url=f"{get_api_url(repository_name)}/{str(release_id)}",
            headers={
                "Authorization": f"token {token}"
            },
            json={
                "tag_name": release_tag,
                "target_commitish": target_commitish,
                "name": release,
                "body": body,
                "draft": False,
                "prerelease": prerelease
            }
        )

    def prepare_artifacts(self, src_artifact: str, dst_artifact :str, workdir: str):
        src_artifact = src_artifact.strip().strip(";")
        patterns = src_artifact.split(";")
        output_files = []
        for pattern in patterns:
            output_files.extend(glob.glob(pattern))

        # Copy artifacts to the temporary workdir.
        output_files = self.copy_files(output_files)

        is_all_regular_files = all(pathlib.Path(file).is_file()
                                   for file in output_files)

        if len(output_files) == 1 and is_all_regular_files:
            # Rename to the target name.
            self.rename_file_in_dir(output_files[0], os.path.join(workdir, dst_artifact))
        elif is_all_regular_files:
            # Don't rename the files
            pass
        else:
            # Rename -> zip to a single .zip file.
            dst_filename = os.path.join(workdir, dst_artifact)
            output_files = [self.zip_files(output_files, dst_filename)]
        return output_files

    def copy_files(self, files, target_dir):
        result = []
        for file in files:
            input_path = pathlib.Path(file)
            if input_path.is_dir():
                result.append(shutil.copytree(str(input_path), target_dir))
            else:
                result.append(shutil.copy(str(input_path), target_dir))
        return result

    def rename_file(self, src, dst):
        os.rename(src, dst)

    def zip_files(self, workdir, dst_zip_file):
        return shutil.make_archive(dst_zip_file, "zip", root_dir=workdir)

    def publish_asset(self, repository_name, asset_path, token):
        # Get current assets.
        asset_name = pathlib.Path(asset_path).name

        r = self.get_assets(repository_name, release_id, token)
        r.raise_for_status()
        current_assets = r.json()
        existing_assets = [asset for asset in current_assets
                           if asset["name"] == asset_name]
        if len(existing_assets) > 0:
            raise RuntimeError(f"Release {release_id} contains more than "
                               f"one asset with name: {package_name}")
        with open(asset_path, "rb") as f:
            data = f.read()
            r = self.upload_asset(repository_name, release_id,
                                  package_name, token, data)
            r.raise_for_status()

    def get_api_url(self, repository_name):
        return f"https://api.github.com/repos/{repository_name}/releases"

    def get_uploads_url(self, repository_name):
        return f"https://uploads.github.com/repos/{repository_name}/releases"

    def get_assets(self, repository_name, release_id, token):
        print("Getting assets")
        return requests.get(
            url=f"{get_api_url(repository_name)}/{str(release_id)}/assets",
            headers={
                "Authorization": f"token {token}"
            }
        )
    def delete_asset(self, repository_name, asset_id, token):
        print("Deleting asset")
        return requests.delete(
            url=get_api_url(repository_name)+"/assets/"+str(asset_id),
            headers={
                'Authorization': f"token {token}"
            },
        )

    def upload_asset(self, repository_name, release_id, asset_name, token,
                     file_to_upload):
        print("Uploading asset")
        return requests.post(
            url=f"{get_uploads_url(repository_name)}/{str(release_id)}/assets?name={asset_name}",
            headers={
                "Content-Type": "application/gzip",
                "Authorization": f"token {token}"
            },
            data=file_to_upload
        )



