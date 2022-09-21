import dagshub

# A basic use case
repo = dagshub.Repo("idonov8", "test-all-file-kinds")
ds = repo.directory("path/to/ds")

with open("test_photo.png", 'rb') as f:
	ds.add(file=f, path="new_folder")
	ds.commit("Add a photo", versioning="dvc")