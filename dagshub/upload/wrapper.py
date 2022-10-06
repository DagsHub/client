import requests
import urllib
import os
from pprint import pprint
from typing import Union
from io import IOBase
from dagshub.upload.debug_logger import logger
from dagshub.common import config

# todo: handle api urls in common package
CONTENT_UPLOAD_URL = "api/v1/repos/{owner}/{reponame}/content/{branch}/{path}"
REPO_INFO_URL = "api/v1/repos/{owner}/{reponame}"


def get_default_branch(src_url, owner, reponame):
    res = requests.get(urllib.parse.urljoin(src_url, REPO_INFO_URL.format(
        owner=owner,
        reponame=reponame
    )))
    return res.json().get('default_branch')


class Repo:
    def __init__(self, owner, name, username=None, password=None, src_url=None, branch=None):
        try:
            self.owner = owner
            self.name = name
            self.src_url = config.host

            if username is not None:
                self.username = username
            elif "DAGSHUB_USERNAME" in os.environ:
                self.username = os.environ["DAGSHUB_USERNAME"]
            else:
                logger.warning(
                    "No DagsHub username specified, defaulting to repo owner. If you're not the owner of the repository you're working on, please speciy your username.")
                self.username = owner
            if password is not None:
                self.password = password
            elif "DAGSHUB_PASSWORD" in os.environ:
                self.password = os.environ["DAGSHUB_PASSWORD"]
            else:
                raise Exception(
                    "Can't find a password/access token. You can set an enviroment variable DAGSHUB_PASSWORD with it or pass it to Repo with 'password'.")
            # TODO: verify token

            if branch is not None:
                self.branch = branch
            else:
                logger.info("Branch wasn't provided. Fetching default branch...")
                self._set_default_branch()
            logger.info(f"Set branch: {self.branch}")

        except Exception as e:
            logger.error(e)
            raise e

    def upload(self, file: Union[str, IOBase], message, versioning=None, new_branch=None, last_commit=None, path=None):
        ds = DataSet(self, ".")
        ds.add(file, path)
        ds.commit(message, versioning, new_branch, last_commit)

    def directory(self, path):
        return DataSet(self, path)

    def get_request_url(self, directory):
        return urllib.parse.urljoin(self.src_url, CONTENT_UPLOAD_URL.format(
            owner=self.owner,
            reponame=self.name,
            branch=self.branch,
            path=urllib.parse.quote(directory, safe="")
        ))

    def _set_default_branch(self):
        try:
            self.branch = get_default_branch(self.src_url, self.owner, self.name)
        except:
            raise Exception(
                "Failed to get default branch for repository. Please specify a branch and make sure repository details are correct.")


class Commit:
    def __init__(self):
        self.choice = "direct"
        self.message = None
        self.summary = None
        self.versioning = "auto"
        self.new_branch = None
        self.last_commit = None


class DataSet:
    def __init__(self, repo: Repo, directory):
        self.files = []
        self.commit_data = Commit()
        self.repo = repo
        self.directory = directory
        self.request_url = self.repo.get_request_url(directory)

    def add(self, file: Union[str, IOBase], path=None):
        try:
            # if path is not provided, fall back to the file name
            if path is None:
                try:
                    path = os.path.basename(os.path.normpath(file if type(file) is str else file.name))
                except:
                    raise Exception(
                        "Could not interpret your file's name. Please specify it in the keyword parameter 'path'.")

            if type(file) is str:
                try:
                    f = open(file, 'rb')
                    self.files.append((path, f))
                    return
                except IsADirectoryError:
                    raise IsADirectoryError("'file' must describe a file, not a directory.")

            self.files.append((path, file))

        except Exception as e:
            logger.error(e)
            raise e

    def _reset_dataset(self):
        self.files = []
        self.commit_data = Commit()

    def commit(self, message, versioning=None, new_branch=None, last_commit=None):
        try:
            data = {}
            if versioning is not None:
                self.commit_data.versioning = versioning
            data["versioning"] = self.commit_data.versioning

            if last_commit is not None:
                self.commit_data.last_commit = last_commit
                data["last_commit"] = self.commit_data.last_commit

            if new_branch is not None:
                self.commit_data.choice = "commit-to-new-branch"
                self.commit_data.new_branch = new_branch

            data["commit_choice"] = self.commit_data.choice

            if self.commit_data.choice == "commit-to-new-branch":
                data["new_branch_name"] = self.commit_data.new_branch

            if message != "":
                self.commit_data.message = message
            else:
                raise Exception("You must provide a valid commit message")
            data["commit_message"] = self.commit_data.message

            if versioning != "git":
                data["is_dvc_dir"] = True

            # Prints for debugging
            logger.debug(f"Request URL: {self.request_url}")
            print("DATA:")
            pprint(data)
            logger.debug("Files:")
            pprint(self.files)
            logger.debug("making request...")
            res = requests.put(
                self.request_url,
                data,
                files=[("files", file) for file in self.files],
                auth=(self.repo.username, self.repo.password))
            logger.debug(f"Response: {res.status_code}")
            print("Response content:")
            try:
                pprint(res.json())
            except Exception:
                pprint(res.content)

            if res.status_code == 200:
                logger.info("Upload finished successfully!")

            self._reset_dataset()

        except Exception as e:
            logger.error(e)
            raise e
