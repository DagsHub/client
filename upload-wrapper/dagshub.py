import requests
from pprint import pprint

# TODO: specify api request URL & stuff

class Repo:
	def __init__(self, owner, name, authToken):
		self.owner = owner
		self.name = name
		self.authToken = authToken

	def directory(self, path):
		return DataSet(self, path)

class Commit:
	choice="direct"
	message=""
	summary=""
	versioning="auto"
	new_branch=""
	def __init__(self):
		return
class DataSet:
	directory = ""
	files = []
	commit_data = Commit()
	def __init__(self, repo, directory):
		self.repo = repo
		self.directory = directory
	
	def add(self, file, path):
		self.files.append((path+file.name, file))
	
	def commit(self, message, versioning=None, new_branch=None):
		data = {}
		if versioning is not None:
			self.commit_data.versioning = versioning
		data["versioning"] = self.commit_data.versioning

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

		data["files"] = ("files", (file for file in self.files))

		pprint(data) # For debugging