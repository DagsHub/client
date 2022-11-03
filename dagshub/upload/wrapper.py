import json

import requests
import urllib
import os
import logging
from typing import Union
from io import IOBase
from dagshub.common import config
from http import HTTPStatus
import dagshub.auth
from dagshub.auth.token_auth import HTTPBearerAuth
from requests.auth import HTTPBasicAuth

# todo: handle api urls in common package
CONTENT_UPLOAD_URL = "api/v1/repos/{owner}/{reponame}/content/{branch}/{path}"
REPO_INFO_URL = "api/v1/repos/{owner}/{reponame}"
DEFAULT_COMMIT_MESSAGE = "Upload files using DagsHub client"
REPO_CREATE_URL = "api/v1/user/repos"
ORG_REPO_CREATE_URL = "api/v1/org/{orgname}/repos"
USER_INFO_URL = "api/v1/user"
logger = logging.getLogger(__name__)


def get_default_branch(src_url, owner, reponame, auth):
    """
    The get_default_branch function takes in a source URL, owner name and repo name.
    It then uses the GitHub API to get the default branch of that repo.
    
    Args:
        src_url[str]: Construct the url for the api call
        owner[str]: Specify the owner of the repo
        reponame[str]: Construct the url to request
        auth[str]: Authenticate the request
    Returns:
        The default branch for a repository
    """
    res = requests.get(urllib.parse.urljoin(src_url, REPO_INFO_URL.format(
        owner=owner,
        reponame=reponame,
    )), auth=auth)
    return res.json().get('default_branch')


def create_repo(repo_name, is_org=False, org_name="", description="", private=False, auto_init=False,
                gitignores="Python", license="", readme="", template="custom"):
    """
    The create_repo function creates a new repository on GitHub account.
    
    Args:
        repo_name[str]: Name of the repository to be created
        is_org[bool]: Create a repo in the user's account
        org_name[bool]: Pass the name of organization reposiotry if is_org = True
        description[str]: Provide the description for the repository
        private[bool]: [by default] creates a public repository. To 
        auto_init[str]: [by default] Create a repository that is not initialized with a readme
        gitignores[str]: Specify the language of the gitignore file that will be used
        license[str]: Specify the license of the repository
        readme[str]: Set the readme
        template[str]: Create a repository with custom files
    Returns:
        A repo object
    
    """
    if template == "":
        template = "none"

    import dagshub.auth
    from dagshub.auth.token_auth import HTTPBearerAuth

    username = config.username
    password = config.password
    if username is not None and password is not None:
        auth = username, password
    else:
        token = config.token or dagshub.auth.get_token()
        if token is not None:
            auth = HTTPBearerAuth(token)

    if auth is None:
        raise RuntimeError("You can't create a repository without being authenticated.")

    if (license != "" or readme != "" or gitignores != "") and template == "none":
        template = "custom"

    data = {
        "name": repo_name,
        "description": description,
        "private": private,
        "auto_init": auto_init,
        "gitignores": gitignores,
        "license": license,
        "readme": readme,
        "project_template": template,
    }

    url = REPO_CREATE_URL
    if is_org is True:
        url = ORG_REPO_CREATE_URL.format(
            orgname=org_name,
        )

    res = requests.post(
        urllib.parse.urljoin(config.host, url),
        data,
        auth=auth,
        headers=config.requests_headers
    )

    if res.status_code != HTTPStatus.CREATED:
        logger.error(f"Response ({res.status_code}):\n"
                     f"{res.content}")
        if res.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
            raise RuntimeError("Repository name is invalid or it already exists.")
        else:
            raise RuntimeError("Failed to create the desired repository.")

    repo = res.json()
    return Repo(owner=repo["owner"]["login"], name=repo["name"], token=token, branch="main")


class Repo:
    def __init__(self, owner, name, username=None, password=None, token=None, branch=None):
        self.owner = owner
        self.name = name
        self.src_url = config.host

        self.username = username or config.username
        self.password = password or config.password
        self.token = token or config.token
        self.branch = branch

        if self.branch is None:
            logger.debug("Branch wasn't provided. Fetching default branch...")
            self._set_default_branch()
        logger.debug(f"Set branch: {self.branch}")

    def upload(self, file: Union[str, IOBase], commit_message=DEFAULT_COMMIT_MESSAGE, path=None, **kwargs):
        """
        The upload function is used to upload files to the repository.
        It takes a file as an argument and returns the url of that file.
        
        Args:
            file:Union[str: Pass a file name or an actual file object
            IOBase]: Specify the file to be uploaded
            commit_message[str]: Specify a commit message for the upload
            path[str]: Specify the path of the file
            **kwargs: Pass in any additional parameters that are needed for the upload function
        Returns:
            A dictionary containing the file_id, commit_message and path of the uploaded file
        
        """
        file_for_upload = DataSet.get_file(file, path)
        self.upload_files([file_for_upload], commit_message=commit_message, **kwargs)

    def upload_files(self,
                     files,
                     directory_path="",
                     commit_message=DEFAULT_COMMIT_MESSAGE,
                     versioning=None,
                     new_branch=None,
                     last_commit=None,
                     force=False):
        """
        The upload_files function uploads a list of files to the specified directory.
        

        Args:
            
            files[list(str)]: list of file paths that will be uploaded to the repository
            directory_path[str]: Specify the directory that you want to upload files to
            commit_message[str]: Pass a commit message to the upload_files function
            versioning[str]: Specify the versioning system to use
            new_branch[str]: Create a new branch
            last_commit[str]: Force the upload of files even if they have not changed
            force[bool]: Force the upload of files that are already in the repo
        Returns:
            A response object
        """

        data = {
            "commit_choice": "direct",
            "commit_summary": commit_message,
            "versioning": versioning,
            "last_commit": last_commit,
            "is_dvc_dir": directory_path != "" and versioning != "git",
        }

        if new_branch is not None:
            data.update({
                "commit_choice": "commit-to-new-branch",
                "new_branch_name": new_branch,
            })

        if force:
            data["last_commit"] = self._get_last_commit()
        logger.warning(f'Uploading {len(files)} files to "{self.full_name}"...')
        res = requests.put(
            self.get_request_url(directory_path),
            data,
            files=[("files", file) for file in files],
            auth=self.auth)
        self._log_upload_details(data, res, files)

    def _log_upload_details(self, data, res, files):
        """
        The _log_upload_details function logs the request URL, data, and files.
        It then logs the response status code and content. If the response is not 200(OK), it will log an error message.
        
        Args:
            data[str]: Pass the data that will be uploaded to the server
            res[dict]: Store the response from the server
            files[list(str)]: Pass the files that are going to be uploaded
        
        Returns:
            The request url, the data sent to the server and the files uploaded
        
        """
        logger.debug(f"Request URL: {res.request.url}\n"
                     f"Data:\n{json.dumps(data, indent=4)}\n"
                     f"Files:\n{json.dumps(list(map(str, files)), indent=4)}")
        try:
            content = json.dumps(res.json(), indent=4)
        except Exception:
            content = res.content.decode("utf-8")

        if res.status_code != HTTPStatus.OK:
            logger.error(f"Response ({res.status_code}):\n"
                         f"{content}")
        else:
            logger.debug(f"Response ({res.status_code})\n")

        if res.status_code == 200:
            logger.warning("Upload finished successfully!")

    @property
    def auth(self):
        """
        The auth function is used to authenticate the user with the dagshub API.It takes in a username and password, or token as arguments. If both are provided, it will use the username and password combination to
         get a token from dagshub's authentication server. Otherwise, if only a token is provided it will be used for authentication.
        
        Returns:
            The httpbasicauth object
        
        """
        if self.username is not None and self.password is not None:
            return HTTPBasicAuth(self.username, self.password)
        token = self.token or dagshub.auth.get_token(code_input_timeout=0)
        return HTTPBearerAuth(token)

    def directory(self, path):
        """
        The directory function returns a DataSet object that represents the directory at the given path.
        
        Args:
            path[str]: Specify the directory that contains all of the images and labels
       
        Returns:
            A dataset object
        
        """
        return DataSet(self, path)

    def get_request_url(self, directory):
        """
        The get_request_url function returns the URL for uploading a file to GitHub.
        
        Args:
            directory[str]: the path to a directory within this repo on GitHub.For example, if you have created your repo in such a 
            way that it has two directories named data and models, then you could pass one of these strings into this function as an argument.
        
        Returns:
            The url of the request to be made
        
        """
        return urllib.parse.urljoin(self.src_url, CONTENT_UPLOAD_URL.format(
            owner=self.owner,
            reponame=self.name,
            branch=self.branch,
            path=urllib.parse.quote(directory, safe="")
        ))

    def _set_default_branch(self):
        """
        The _set_default_branch function is used to set the default branch for a repository.
        It first tries to get the default branch from GitHub, but if it fails, then an error message is raised.
        
        
        Returns:
            The branch name of the repository
        
        """
        try:
            self.branch = get_default_branch(self.src_url, self.owner, self.name, self.auth)
        except Exception:
            raise RuntimeError(
                "Failed to get default branch for repository. "
                "Please specify a branch and make sure repository details are correct.")

    @property
    def full_name(self):
        """
        The full_name function returns the full name of a repository.
        
        Returns:
            The concatenation of the owner and name attributes
        
        """
        return f"{self.owner}/{self.name}"


class DataSet:
    def __init__(self, repo: Repo, directory: str):
        """
        The __init__ function is called when a new instance of the class is created.
        It initializes all of the variables and sets them to their default values.
        
        Args:
            repo[Repo object]: Pass a Repo object
            directory[str]: Specify the directory of the repository
        
        Returns:
            A dictionary of files
        
        """
        self.files = {}
        self.repo = repo
        self.directory = self._clean_directory_name(directory)
        self.request_url = self.repo.get_request_url(directory)

    def add(self, file: Union[str, IOBase], path=None):
        
        """
        The add function adds a file to the list of files that will be uploaded.          
        
        Args:
            file[str]: Name of the file
            path[str]: Specify path to upload the file
        
        Returns:
            The function returns nothing.
        
        """
        path, file = self.get_file(file, path)
        if file is not None:
            if path in self.files:
                logger.warning(f"File already staged for upload on path \"{path}\". Overwriting")
            self.files[path] = (path, file)

    @staticmethod
    def _clean_directory_name(directory: str):
        """
        The _clean_directory_name function takes a directory name as an argument and returns the normalized path of that directory.
        For example, if the input is ../../../ then it will return /. If the input is ./ then it will return ..
        If there are any other characters in the string, they will be ignored and only alphanumeric characters (a-zA-Z0-9) 
        will be kept.
        
        Args:
            directory[str]: Specify the directory that will be cleaned
        
        Returns:
            The directory name with the path separator normalized to a forward slash
        
        """
        return os.path.normpath(directory)

    @staticmethod
    def get_file(file: Union[str, IOBase], path=None):
        """
        The get_file function is a helper function that takes in either a string or an IOBase object and returns
        a tuple containing the file's name and the file itself. If no path is provided, it will default to the name of
        the file. This function also handles exceptions such as when you try to pass in a directory instead of a file.
        
        file[str]: Name of the file 
        path[str]: Specify the path of the file
        Returns:
            A tuple of the path and a file object
        
        """
        try:
            # if path is not provided, fall back to the file name
            if path is None:
                try:
                    path = os.path.basename(os.path.normpath(file if type(file) is str else file.name))
                except Exception:
                    raise RuntimeError(
                        "Could not interpret your file's name. Please specify it in the keyword parameter 'path'.")

            if type(file) is str:
                try:
                    f = open(file, 'rb')
                    return path, f
                except IsADirectoryError:
                    raise IsADirectoryError("'file' must describe a file, not a directory.")

            return path, file

        except Exception as e:
            logger.error(e)
            raise e

    def _reset_dataset(self):
        """
        The _reset_dataset function clears the files attribute of a Dataset object.
        
        
        
        Returns:
            The empty list
        
        """
        self.files.clear()

    def commit(self, commit_message=DEFAULT_COMMIT_MESSAGE, *args, **kwargs):
        """
        The commit function is used to commit the files in the dataset.
        It takes a commit message as an argument, which can be set to None if no message is required.
        The function returns nothing.
        
        Args:

            commit_message[str]: Pass a commit message to the upload_files function
            *args: Pass a non-keyworded, variable-length argument list
            **kwargs: Pass additional parameters to the function
        
        Returns:
            The commit_message
        
        """
        file_list = list(self.files.values())
        self.repo.upload_files(file_list, self.directory, commit_message=commit_message, *args, **kwargs)
        self._reset_dataset()

    def _get_last_commit(self):
        """
        The _get_last_commit function returns the last commit sha for a given branch.
        It is used to check if there are any new commits in the repo since we last ran our dag.
        
        
        Returns:
            The commit sha for the branch of the repo
        
        """
        api_path = f"api/v1/repos/{self.repo.full_name}/branches/{self.repo.branch}"
        api_url = urllib.parse.urljoin(self.repo.src_url, api_path)
        res = requests.get(api_url)
        if res.status_code == HTTPStatus.OK:
            content = res.json()
            try:
                return content["commit"]["id"]
            except KeyError:
                logger.error(f"Cannot get commit sha for branch '{self.repo.branch}'")
        return ""
