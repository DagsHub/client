import requests

class Repo:
	def __init__(self, owner, name, authToken):
		self.owner = owner
		self.name = name
		self.authToken = authToken

	def directory(self, path):
		pass # TODO: implement, returns a DataSet object

class DataSet:
	repo = Repo()
	directory = ""
	files = []
	versioning = "auto"
	def __init__(self, repo, directory, files, versioning):
		self.repo = repo
		self.directory = directory
		self.files = files
		self.versioning = versioning
	
	def add(self, file, path):
		pass # TODO: implement
	
	def commit(self, message, versioning=None):
		pass # TODO: implement