import requests
import urllib
import os
from pprint import pprint

DEFAULT_SOURCE_URL = "https://dagshub.com/"
CONTENT_UPLOAD_URL = "api/v1/repos/{owner}/{reponame}/content/{branch}/{path}"
REPO_INFO_URL = "api/v1/repos/{owner}/{reponame}"

class Repo:
	src_url = DEFAULT_SOURCE_URL
	def __init__(self, owner, name, authToken=None, src_url=None, branch=None):
		self.owner = owner
		self.name = name

		if authToken != None:
			self.authToken = authToken
		elif "ACCESS_TOKEN" in os.environ:
			self.authToken = os.environ["ACCESS_TOKEN"]
		else:
			raise Exception("Can't find access token. Please set enviroment variable ACCESS_TOKEN with a DagsHub access token")
		# TODO: verify token
		
		if src_url != None:
			self.src_url = src_url
		elif "SRC_URL" in os.environ:
			self.src_url = os.environ["SRC_URL"]

		if branch != None:
			self.branch = branch
		else:
			# Find default branch and set it if not specified
			res = requests.get(urllib.parse.urljoin(self.src_url, REPO_INFO_URL.format(
				owner=self.owner,
				reponame=self.name
				)))
			try:
				self.branch = res.json().get('default_branch')
				print("Set default branch: ", self.branch)
			except:
				raise Exception("Failed to get default branch for repository. Please specify a branch and make sure repository details are correct.")


	def directory(self, path):
		return DataSet(self, path)

class Commit:
	choice="direct"
	message=""
	summary=""
	versioning="auto"
	new_branch=""
	last_commit=""
	def __init__(self):
		return

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
		if target_dir != None:
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
		if versioning != None:
			self.commit_data.versioning = versioning
		data["versioning"] = self.commit_data.versioning

		if last_commit != None:
			self.commit_data.last_commit = last_commit
		data["last_commit"] = self.commit_data.last_commit

		if new_branch != None:
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