import requests
import urllib
import os
from pprint import pprint

DEFAULT_SOURCE_URL = "https://dagshub.com/"
CONTENT_UPLOAD_URL = "api/v1/repos/{owner}/{reponame}/content/{branch}/{path}"
REPO_INFO_URL = "api/v1/repos/{owner}/{reponame}"

def get_default_branch(src_url, owner, reponame):
	res = requests.get(urllib.parse.urljoin(src_url, REPO_INFO_URL.format(
		owner=owner,
		reponame=reponame
		)))
	return res.json().get('default_branch')

class Repo:
	src_url = DEFAULT_SOURCE_URL
	def __init__(self, owner, name, authToken=None, src_url=None, branch=None):
		self.owner = owner
		self.name = name
		self.src_url = src_url if src_url is not None else os.environ.get("SRC_URL")

		if authToken is not None:
			self.authToken = authToken
		elif "ACCESS_TOKEN" in os.environ:
			self.authToken = os.environ["ACCESS_TOKEN"]
		else:
			raise Exception("Can't find access token. Please set enviroment variable ACCESS_TOKEN with a DagsHub access token")
		# TODO: verify token

		if branch is not None:
			self.branch = branch
		else:
			print("Branch wasn't provided. Fetching default branch.")
			self._set_default_branch()
		print("Set branch: ", self.branch)

	def directory(self, path):
		return DataSet(self, path)
		

	def _set_default_branch(self):
		try:
			self.branch = get_default_branch(self.src_url, self.owner, self.name)
		except:
			raise Exception("Failed to get default branch for repository. Please specify a branch and make sure repository details are correct.")

class Commit:
	def __init__(self):
		self.choice="direct"
		self.message=""
		self.summary=""
		self.versioning="auto"
		self.new_branch=""
		self.last_commit=""

class DataSet:
	directory = ""
	files = []
	commit_data = Commit()
	def __init__(self, repo, directory):
		self.repo = repo
		self.directory = directory
		self.request_url = urllib.parse.urljoin(repo.src_url, CONTENT_UPLOAD_URL.format(
			owner=repo.owner,
			reponame=repo.name,
			branch=repo.branch,
			path=urllib.parse.quote(directory, safe="")
		))

	def add(self, file, path=".", target_dir=None):
		# path is the full target path, including the file name
		if target_dir is not None:
			if path != ".":
				raise Exception("You must provide either a path or a target_dir. You can't provide both")
			path = os.path.join(target_dir, os.path.basename(os.path.normpath(file if type(file) is str else file.name)))

		if type(file) is str:
			try:
				f = open(file, 'rb')
				self.files.append((path, f))
				return
			except IsADirectoryError:
				raise IsADirectoryError("'file' must describe a file, not a directory.")

		self.files.append((path, file))

	def commit(self, message, versioning=None, new_branch=None, last_commit=None):
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

		# Prints for debugging
		print("URL: ", self.request_url)
		print("DATA:")
		pprint(data)
		print("Files:")
		pprint(self.files)
		print("making request...")
		res = requests.put(
			self.request_url, 
			data, 
			files=[("files", file) for file in self.files], 
			headers={'Authorization': 'token ' + self.repo.authToken})
		print("Response: ", res.status_code)
		pprint(res.content)

		if res.status_code == 200:
			print("Upload finished successfully!")