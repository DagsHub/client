from dagshub.common import config
import urllib
import requests


def get_default_branch(owner, reponame, auth, host=config.host):
    """
    The get_default_branch function returns the default branch of a given repository.
    
    :param owner(str): Specify the owner of the repository
    :param reponame (str): Specify the name of the repository
    :param auth (str): Authenticate the user with github
    :param host (str): Specify the host to be used
    :return: The default branch of the given repository
    """
    res = requests.get(urllib.parse.urljoin(host, config.REPO_INFO_URL.format(
        owner=owner,
        reponame=reponame,
    )), auth=auth)
    return res.json().get('default_branch')
